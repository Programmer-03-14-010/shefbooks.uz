import mimetypes
import os
import re

from django.http import HttpResponse, StreamingHttpResponse


def ranged_file_response(request, path, filename, inline=True):
    """Faylni Range (206) qo'llab-quvvatlagan holda uzatadi — audio'ni oldinga-orqaga surish uchun kerak."""
    size = os.path.getsize(path)
    ctype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    start, end, status = 0, size - 1, 200

    match = re.match(r'bytes=(\d*)-(\d*)$', request.headers.get('Range', '').strip())
    if match and size:
        s, e = match.groups()
        if s == '' and e:
            start = max(0, size - int(e))
        else:
            start = int(s) if s else 0
            if e:
                end = min(int(e), size - 1)
        if start > end or start >= size:
            resp = HttpResponse(status=416)
            resp['Content-Range'] = f'bytes */{size}'
            return resp
        status = 206

    length = end - start + 1

    def chunks():
        with open(path, 'rb') as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                data = f.read(min(65536, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data

    resp = StreamingHttpResponse(chunks(), status=status, content_type=ctype)
    resp['Content-Length'] = str(length)
    resp['Accept-Ranges'] = 'bytes'
    if status == 206:
        resp['Content-Range'] = f'bytes {start}-{end}/{size}'
    safe_name = filename.replace('"', '')
    resp['Content-Disposition'] = f'{"inline" if inline else "attachment"}; filename="{safe_name}"'
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Cache-Control'] = 'private, no-store'
    return resp
