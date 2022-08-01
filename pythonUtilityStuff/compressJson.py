import brotli
import json

with open('./soapStoneTranslatorJs/er/soapstoneTranslatorER-LSH3-696HashOnly.html', 'rb') as f:
    hashTables = f.read()
    print(len(hashTables))
    compressed = brotli.compress(hashTables, 0, 11, 24, 0)
    # f1 = f.encode('ascii')

# # Decompress a Brotli-compressed payload in one go.
# decompressed_data = brotli.decompress(compressed_data)
#
# # Alternatively, you can do incremental decompression.
# d = brotli.Decompressor()
# for chunk in chunks_of_compressed_data:
#     some_uncompressed_data = d.decompress(chunk)
#
# remaining_data = d.flush()

# You can compress data too.



f = open('./soapstoneTranslatorER-LSH3-696HashOnly.html.br', 'wb')
f.write(compressed)
f.close()


