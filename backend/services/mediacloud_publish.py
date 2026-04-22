"""MediaCloud publish service for writing reviewed sources to collections."""
import json
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from config import get_config

logger = logging.getLogger(__name__)

# Sentinel: update_source_metadata should fetch Directory record (default).
_DIRECTORY_RECORD_NOT_PASSED = object()

try:
    from mediacloud.mgmt import DirectoryManagementApi
except Exception:  # pragma: no cover - import failure handled at runtime
    DirectoryManagementApi = None

try:
    from mediacloud.api import DirectoryApi
except Exception:  # pragma: no cover - import failure handled at runtime
    DirectoryApi = None


def _normalize_homepage(homepage):
    homepage = (homepage or "").strip()
    if not homepage:
        return ""
    homepage = homepage.rstrip("/")
    try:
        parsed = urlparse(homepage)
        if parsed.scheme and parsed.netloc:
            scheme = (parsed.scheme or "").lower()
            netloc = (parsed.netloc or "").lower()
            path = (parsed.path or "").rstrip("/")
            query = f"?{parsed.query}" if parsed.query else ""
            return f"{scheme}://{netloc}{path}{query}"
    except Exception:
        pass
    return homepage.lower()


class MediaCloudPublishService:
    """Service for write operations against MediaCloud directory management API."""

    @staticmethod
    def describe_client_exception(exc):
        """
        Best-effort string for MediaCloud client / HTTP failures.
        APIResponseError.__str__ often omits Django 'detail' (client uses data.get('note')).
        """
        if exc is None:
            return ''
        parts = []
        resp = getattr(exc, 'response', None)
        status = getattr(resp, 'status_code', None) if resp is not None else None
        if status:
            parts.append(f'HTTP {status}')
        data = getattr(exc, 'data', None)
        if isinstance(data, dict):
            detail = data.get('detail')
            if isinstance(detail, list):
                parts.append('; '.join(str(x) for x in detail))
            elif isinstance(detail, dict):
                try:
                    parts.append(json.dumps(detail, default=str))
                except Exception:
                    parts.append(str(detail))
            elif detail is not None:
                parts.append(str(detail))
            note = data.get('note')
            if note is not None and str(note) != str(detail):
                parts.append(str(note))
        generic = str(exc).strip()
        if generic and generic not in ' '.join(parts):
            parts.append(generic)
        return ' · '.join(parts) if parts else repr(exc)

    def __init__(self, api_token):
        if not api_token or not str(api_token).strip():
            raise ValueError("api_token is required")

        if DirectoryManagementApi is None:
            raise RuntimeError(
                "MediaCloud directory management API is unavailable in this environment. "
                "Please update the mediacloud client package."
            )

        config = get_config()
        base_url = (config.MEDIACLOUD_UPLOAD_BASE_URL or "").strip() or None

        # Support both client variants (with/without configurable base_url).
        if base_url is not None:
            try:
                self.mgmt = DirectoryManagementApi(api_token, base_url=base_url)
            except TypeError:
                try:
                    self.mgmt = DirectoryManagementApi(api_token, base_url)
                except TypeError:
                    self.mgmt = DirectoryManagementApi(api_token)
        else:
            self.mgmt = DirectoryManagementApi(api_token)

        if base_url is not None:
            self.mgmt.BASE_API_URL = self._normalize_api_base_url(base_url)
        self.directory = None
        if DirectoryApi is not None:
            self.directory = DirectoryApi(api_token)
            if base_url is not None:
                self.directory.BASE_API_URL = self._normalize_api_base_url(base_url)
        self.api_base_url = getattr(self.mgmt, "BASE_API_URL", None)

    @staticmethod
    def _normalize_api_base_url(raw_url):
        """
        Normalize MediaCloud API base URL to include trailing /api/.
        Accepts values like:
        - https://search.mediacloud.org
        - https://search.mediacloud.org/
        - https://search.mediacloud.org/api
        - https://search.mediacloud.org/api/
        """
        value = (raw_url or "").strip()
        if not value:
            return value
        value = value.rstrip("/")
        if value.endswith("/api"):
            return f"{value}/"
        return f"{value}/api/"

    def create_collection(self, name):
        name = (name or "").strip()
        if not name:
            raise ValueError("Collection name is required")
        created = self.mgmt.collection_create(name=name, notes=self._audit_note("created"))
        collection_id = (
            created.get("id")
            or created.get("collection_id")
            or created.get("tags_id")
        )
        if not collection_id:
            raise RuntimeError("MediaCloud did not return collection id for created collection")
        return int(collection_id), created

    def append_update_note(self, collection_id):
        collection_id = int(collection_id)
        existing_notes = ""
        if self.directory is not None:
            try:
                details = self.directory.collection(collection_id)
                existing_notes = str(details.get("notes") or "").strip()
            except Exception:
                existing_notes = ""

        update_note = self._audit_note("updated")
        if existing_notes:
            merged_notes = f"{existing_notes}\n{update_note}"
        else:
            merged_notes = update_note

        return self.mgmt.collection_update(collection_id=collection_id, notes=merged_notes)

    @staticmethod
    def _audit_note(action):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"{action} via Collection Review Tool @ {ts}"

    def create_source(self, item):
        metadata = {}
        if item.source_metadata:
            try:
                metadata = json.loads(item.source_metadata) or {}
            except Exception:
                metadata = {}

        payload = {
            "name": (item.source_label or "").strip(),
            "homepage": (item.source_homepage or "").strip(),
        }
        if not payload["name"] or not payload["homepage"]:
            raise ValueError("New source requires source_label and source_homepage")

        for key in ("primary_language", "pub_country", "pub_state"):
            val = metadata.get(key)
            if val is not None and str(val).strip() != "":
                payload[key] = val

        created = self.mgmt.source_create(**payload)
        source_id = (
            created.get("id")
            or created.get("source_id")
            or created.get("media_id")
        )
        if not source_id:
            raise RuntimeError("MediaCloud did not return source id for created source")
        return int(source_id), created

    def ensure_source_in_collection(self, source_id, collection_id):
        return self.mgmt.source_collection_create(
            source_id=int(source_id),
            collection_id=int(collection_id),
        )

    def remove_source_from_collection(self, source_id, collection_id):
        return self.mgmt.source_collection_delete(
            source_id=int(source_id),
            collection_id=int(collection_id),
        )

    METADATA_KEYS = ('primary_language', 'pub_country', 'pub_state')

    # Directory / sources API payloads vary by deployment; try several keys and nested shapes.
    _DIRECTORY_LANGUAGE_KEYS = (
        'primary_language',
        'language',
        'primaryLanguage',
        'lang',
        'locale',
        'default_language',
        'media_primary_language',
    )
    _DIRECTORY_COUNTRY_KEYS = (
        'pub_country',
        'country',
        'pubCountry',
        'country_code',
        'countryCode',
        'publication_country',
    )
    _DIRECTORY_STATE_KEYS = (
        'pub_state',
        'state',
        'pubState',
        'publication_state',
        'administrative_division',
    )

    @staticmethod
    def normalize_metadata_scalar(val):
        if val is None:
            return ''
        return str(val).strip()

    @staticmethod
    def _coerce_directory_metadata_value(val):
        """Normalize API values that may be strings or nested objects (e.g. {code: 'en'})."""
        if val is None:
            return None
        if isinstance(val, dict):
            for subk in ('code', 'id', 'name', 'label', 'value', 'iso_code'):
                inner = val.get(subk)
                if inner is None or isinstance(inner, dict):
                    continue
                s = str(inner).strip()
                if s:
                    return s
            return None
        if isinstance(val, (list, tuple)):
            for el in val:
                if el is None:
                    continue
                if isinstance(el, dict):
                    inner = MediaCloudPublishService._coerce_directory_metadata_value(el)
                    if inner:
                        return inner
                else:
                    s = str(el).strip()
                    if s:
                        return s
            return None
        s = str(val).strip()
        return s if s else None

    @classmethod
    def _pick_directory_field(cls, record, candidate_keys):
        if not record:
            return ''
        for name in candidate_keys:
            raw = record.get(name)
            if raw is None:
                continue
            coerced = cls._coerce_directory_metadata_value(raw)
            if coerced is not None:
                return cls.normalize_metadata_scalar(coerced)
        return ''

    @classmethod
    def metadata_fields_from_directory_record(cls, record):
        """Extract comparable metadata fields from a DirectoryApi source record."""
        if not record:
            return {k: '' for k in cls.METADATA_KEYS}
        containers = [record]
        for nk in ('metadata', 'details', 'source_metadata'):
            sub = record.get(nk)
            if isinstance(sub, dict):
                containers.append(sub)

        def pick(candidates):
            for container in containers:
                val = cls._pick_directory_field(container, candidates)
                if val:
                    return val
            return ''

        return {
            'primary_language': pick(cls._DIRECTORY_LANGUAGE_KEYS),
            'pub_country': pick(cls._DIRECTORY_COUNTRY_KEYS),
            'pub_state': pick(cls._DIRECTORY_STATE_KEYS),
        }

    @classmethod
    def prune_metadata_patch_to_changes(cls, desired_patch, remote_fields):
        """Return only keys whose desired value differs from remote (normalized string compare)."""
        if not desired_patch:
            return {}
        pruned = {}
        for key in cls.METADATA_KEYS:
            if key not in desired_patch:
                continue
            want = cls.normalize_metadata_scalar(desired_patch.get(key))
            if not want:
                continue
            got = cls.normalize_metadata_scalar((remote_fields or {}).get(key, ''))
            if want != got:
                pruned[key] = want
        return pruned

    def fetch_source_directory_record(self, source_id):
        """
        Fetch one source dict from DirectoryApi (read path), or None if unavailable / not found.

        Note: DirectoryApi.source_list() does not accept source_id (only collection_id/name/platform).
        Single-source reads must use DirectoryApi.source(source_id).
        """
        if self.directory is None:
            return None
        sid = int(source_id)
        try:
            if hasattr(self.directory, 'source'):
                rec = self.directory.source(sid)
                if not rec:
                    return None
                return dict(rec)
            # Very old clients: no direct source() — cannot reliably filter source_list.
            return None
        except Exception:
            return None

    def metadata_patch_needed_for_source(self, item):
        """
        Desired metadata PATCH for an existing source, pruned against current MediaCloud values.

        Returns (patch_dict, remote_fields_or_none, directory_record_or_none).
        When directory_record_or_none is a dict, callers may pass it to update_source_metadata
        to avoid a second DirectoryApi.source() round-trip.
        """
        desired = self.metadata_patch_from_item(item)
        if not desired:
            return {}, None, None
        record = self.fetch_source_directory_record(item.source_id)
        if record is None:
            return desired, None, None
        remote = self.metadata_fields_from_directory_record(record)
        return self.prune_metadata_patch_to_changes(desired, remote), remote, record

    @staticmethod
    def metadata_patch_from_item(item):
        """Non-empty metadata fields from ReviewItem.source_metadata suitable for MediaCloud source_update."""
        if not item.source_metadata:
            return {}
        try:
            meta = json.loads(item.source_metadata) or {}
        except Exception:
            return {}
        patch = {}
        for key in MediaCloudPublishService.METADATA_KEYS:
            val = meta.get(key)
            if val is not None and str(val).strip() != '':
                patch[key] = str(val).strip()
        return patch

    @staticmethod
    def _homepage_and_label_from_item(item):
        """Homepage and label from review row (fallback when Directory read is unavailable)."""
        label = (item.source_label or '').strip()
        homepage = (item.source_homepage or '').strip()
        meta = {}
        if item.source_metadata:
            try:
                meta = json.loads(item.source_metadata) or {}
            except Exception:
                meta = {}
        if not homepage:
            homepage = (
                (meta.get('homepage') or meta.get('url') or meta.get('media_url') or '')
            ).strip()
        if not label:
            label = (meta.get('name') or meta.get('label') or '').strip()
        return homepage, label

    _IDENTITY_KEYS_FOR_SOURCE_UPDATE = (
        'platform',
        'url_search_string',
        'notes',
        'media_type',
    )

    @staticmethod
    def _kwargs_for_log(kwargs):
        """Avoid huge log lines (e.g. collection notes copied onto sources)."""
        if not kwargs:
            return {}
        out = dict(kwargs)
        notes = out.get('notes')
        if notes is not None and len(str(notes)) > 240:
            out['notes'] = str(notes)[:240] + '...'
        return out

    @classmethod
    def source_identity_kwargs_from_directory_record(cls, record):
        """
        Copy non-metadata fields exactly as returned by DirectoryApi.source() so PATCH
        does not replace MediaCloud's canonical name/homepage (which triggers validation errors).
        """
        if not record:
            return {}
        out = {}
        homepage = (
            cls._normalize_str_field(record.get('homepage'))
            or cls._normalize_str_field(record.get('url'))
            or cls._normalize_str_field(record.get('media_url'))
        )
        if homepage:
            out['homepage'] = homepage
        name = cls._normalize_str_field(record.get('name'))
        label = cls._normalize_str_field(record.get('label'))
        if name:
            out['name'] = name
        if label:
            out['label'] = label
        if not out.get('name') and label:
            out['name'] = label
        if not out.get('label') and name:
            out['label'] = name
        for key in cls._IDENTITY_KEYS_FOR_SOURCE_UPDATE:
            v = cls._normalize_str_field(record.get(key))
            if v:
                out[key] = v
        return out

    @staticmethod
    def _normalize_str_field(val):
        if val is None:
            return None
        s = str(val).strip()
        return s if s else None

    def update_source_metadata(self, source_id, item, patch, directory_record=_DIRECTORY_RECORD_NOT_PASSED):
        """
        PATCH source metadata (language / geography).

        Sends identity fields (name, label, homepage, …) from a fresh DirectoryApi.source()
        read, then overlays only primary_language / pub_country / pub_state from the patch.
        Avoids review-tool strings that diverge from MediaCloud's canonicalized homepage/name.

        Pass directory_record=dict from metadata_patch_needed_for_source to skip a duplicate GET.
        Pass directory_record=None when the read already failed and only review fallbacks apply.
        """
        if not patch:
            return None
        meta_kwargs = {k: patch[k] for k in self.METADATA_KEYS if k in patch}
        if not meta_kwargs:
            return None
        if directory_record is _DIRECTORY_RECORD_NOT_PASSED:
            record = self.fetch_source_directory_record(source_id)
        else:
            record = directory_record
        kwargs = dict(self.source_identity_kwargs_from_directory_record(record)) if record else {}
        kwargs.update(meta_kwargs)
        if not kwargs.get('homepage'):
            homepage, _lbl = self._homepage_and_label_from_item(item)
            if homepage:
                kwargs['homepage'] = homepage
        if not kwargs.get('name') and not kwargs.get('label'):
            _hp, label = self._homepage_and_label_from_item(item)
            if label:
                kwargs['name'] = label
                kwargs['label'] = label
        try:
            return self.mgmt.source_update(source_id=int(source_id), **kwargs)
        except Exception as first_error:
            desc = self.describe_client_exception(first_error)
            logger.warning(
                'MediaCloud source_update failed source_id=%s kwargs=%s: %s',
                source_id,
                self._kwargs_for_log(kwargs),
                desc,
                exc_info=True,
            )
            raise

    def reduce_items_for_publish(self, items):
        """
        Reduce possibly-duplicate rows across queues to one action per source/homepage.
        Last item by id wins when duplicate keys appear.
        """
        reduced = {}
        for item in sorted(items, key=lambda x: x.id):
            if item.source_id is not None:
                key = f"source:{int(item.source_id)}"
            else:
                key = f"new:{_normalize_homepage(item.source_homepage)}"
            if key.endswith("new:"):
                key = f"item:{item.id}"
            reduced[key] = item
        return list(reduced.values())

    def preflight(self):
        """Validate token against target API and return profile details when possible."""
        profile = self.mgmt.user_profile()
        return {
            "ok": True,
            "api_base_url": self.api_base_url,
            "profile": {
                "email": profile.get("email"),
                "username": profile.get("username"),
                "roles": profile.get("roles") or [],
            },
        }
