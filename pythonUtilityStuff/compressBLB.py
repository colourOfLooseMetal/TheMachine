import gzip, shutil
fname = './test.wasm'
src = open(fname, 'rb')
dest = gzip.open(fname+".gz", 'wb', compresslevel=1)

shutil.copyfileobj(src, dest)

src.close()
dest.close()