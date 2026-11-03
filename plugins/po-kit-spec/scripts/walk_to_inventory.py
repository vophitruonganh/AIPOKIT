#!/usr/bin/env python3
"""Turn autowalk output (walk format) into inventory rows, so the recon agent never types table rows.
Usage: walk_to_inventory.py <walk.txt> [<walk2.txt> ...] --prefix DW-8 [--start 1] [--role "Phòng khám"] [--out inventory.X.md]

Walk format (what AW.walk() returns; the agent saves it as is, then edits only what it must):
  ## <screen route> | <feature N.M>        a screen; the feature applies to every row below until the next '##'
  ### <path> [!<status>]                   what opened inside it: Tab: x / Dropdown: x / Row menu: x / Dialog: x / Page: x
  kind|label[|status[|feature]]            one element; status/feature override the defaults
  option|x                                 options of the Dropdown / Row menu above (one row: option-list or row-action)
  api|... note|...                         ignored here (api lines are listed at the end of the report for api.md)
  - a line starting with '-' is dropped (the agent deletes an element by prefixing '-')
Defaults: Status Explored; '!Opened read-only' on a Dialog/Page line applies to its rows; a button whose label matches
the danger list gets 'Safety-blocked: real effect' (edit it to the exact rule when needed).
Kinds: input/textarea/checkbox/radio/toggle/upload -> form-field (filter or search on the main screen), heading -> header
(only the first of each screen and dialog titles), Go to ... page -> pagination, Dialog -> modal row."""
import sys, re, argparse

DANGER = re.compile(r'lưu|xoá|xóa|thu tiền|đã thu|gửi|ký số|^ký|xuất|tải về|tải xuống|^in\b|in phiếu|đăng xuất|nâng cấp|thanh toán|hoàn tất|xác nhận|kích hoạt|duyệt|từ chối|^bán|gọi|nhận thông báo|đồng ý|áp dụng|cập nhật|phát hành|huỷ|hủy|bắt đầu|kết thúc|delete|save|submit|logout|confirm|send|export|download|print|approve|reject|upgrade', re.I)
CLOSE = re.compile(r'^(close|đóng|hủy|huỷ|quay lại|trở lại|cancel|back|see-password)$', re.I)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--prefix', required=True)
    ap.add_argument('--start', type=int, default=1); ap.add_argument('--role', default='User'); ap.add_argument('--out')
    a = ap.parse_args()
    rows, api, n = [], [], a.start
    for fn in a.files:
        screen, feat, path, pstat, opts, okind = '', '', 'Main', '', None, ''

        def flush():
            nonlocal opts
            if opts and opts[1]:
                lab = opts[0] + ': ' + ' / '.join(opts[1])
                rows.append((screen, path, okind, lab[:180], pstat or 'Explored', feat))
            opts = None
        for raw in open(fn, encoding='utf-8'):
            ln = raw.rstrip('\n')
            if not ln.strip() or ln.startswith('-'): continue
            if ln.startswith('## '):
                flush(); m = ln[3:].split('|'); screen = m[0].strip(); feat = m[1].strip() if len(m) > 1 else 'global'
                path, pstat = 'Main', ''; continue
            if ln.startswith('### '):
                flush(); h = ln[4:]; st = ''
                if '!' in h: h, st = h.split('!', 1); h, st = h.strip(), st.strip()
                if h == 'API': path = 'API'; continue
                kind, _, name = h.partition(':'); name = name.strip()
                if kind in ('Dropdown', 'Row menu'):   # options of a control on the current path: keep its status
                    opts = [name, []]; okind = 'option-list' if kind == 'Dropdown' else 'row-action'
                    continue
                pstat = st
                path = 'Main > ' + h
                if kind == 'Dialog': rows.append((screen, path, 'modal', name, pstat or 'Opened read-only', feat))
                continue
            parts = ln.split('|'); kind = parts[0].strip(); label = parts[1].strip() if len(parts) > 1 else ''
            if kind == 'api': api.append(label); continue
            if kind == 'note': continue
            if kind == 'option':
                if opts is not None: opts[1].append(label)
                continue
            flush()
            st = parts[2].strip() if len(parts) > 2 and parts[2].strip() else ''
            fe = parts[3].strip() if len(parts) > 3 and parts[3].strip() else feat
            if kind == 'link' and ' -> ' in label: label = label.split(' -> ')[0].strip()   # the route is not part of the label the spec must quote
            if not label: continue
            if kind == 'button' and CLOSE.match(label): continue
            if kind == 'heading': kind = 'header'
            elif kind in ('input', 'textarea', 'checkbox', 'radio', 'toggle', 'upload'):
                kind = 'form-field' if path != 'Main' else ('search' if re.search(r'tìm|search', label, re.I) else 'filter')
            elif kind == 'button' and re.match(r'Go to (first|previous|next|last) page', label): kind = 'pagination'
            elif kind not in ('button', 'link', 'dropdown', 'column', 'tab'): kind = 'state'
            if not st:
                st = pstat or 'Explored'
                if kind == 'button' and DANGER.search(label): st = 'Safety-blocked: real effect'
            rows.append((screen, path, kind, label, st, fe))
        flush()
    seen, out = set(), []
    for r in rows:
        k = (r[0], r[1], r[2], r[3].lower())
        if k in seen: continue
        seen.add(k); out.append(r)
    lines = ['| ID | Screen | Path | Kind | Label | Role | Status | Feature |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for s, p, k, l, st, fe in out:
        lines.append('| %s%03d | %s | %s | %s | %s | %s | %s | %s |' % (a.prefix, n, s, p, k, l.replace('|', '/'), a.role, st, fe)); n += 1
    text = '\n'.join(lines) + '\n'
    if a.out: open(a.out, 'w', encoding='utf-8').write(text)
    else: sys.stdout.write(text)
    sys.stderr.write('rows %d (next id %s%03d)\n' % (len(out), a.prefix, n))
    if api: sys.stderr.write('api:\n' + '\n'.join(sorted(set(api))) + '\n')


if __name__ == '__main__':
    main()
