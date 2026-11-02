import json,base64,glob,os,sys
out=sys.argv[1]
for f in glob.glob('/root/.claude/projects/-home-claude/5058815f-c3e9-5e36-b61d-db422c4a157e/tool-results/mcp-Claude_Docs-export-*.txt'):
    arr=json.load(open(f))
    for it in arr:
        t=it.get('text','')
        if t.startswith('{"verdict"'):
            d=json.loads(t)['data']
            p=os.path.join(out,d['name'])
            open(p,'wb').write(base64.b64decode(d['bytes_b64']))
            print(d['name'],d['bytes'])
