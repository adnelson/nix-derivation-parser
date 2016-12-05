import os
from servenix.client.sendnix import StoreObjectSender

import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

path = "/opt/ns/nix/store/fw8344g7xrmf7bp248xqqkncda3i26s6-hello-2.10"

sender = StoreObjectSender(os.environ["NIX_REPO_HTTP"])

sender.fetch_object(path)

# from servenix.common.narinfo import NarInfo

# raw = 'Compression: xz\nNarHash: sha256:090909nn09rvhz4hd23wjsbhhb74xrip2rfhcb5kvp2p4d9cmf7s\nFileSize: 40304\nURL: nar/fw8344g7xrmf7bp248xqqkncda3i26s6.nar.xz\nFileHash: sha256:1kdsgvnxg0z1kxs2n8g8jzs7zjspfp7mxpid0xv8nz7jpdwkyj8w\nReferences: 42yshyai1hxbwb5w9lz3hv077pqzfqkj-glibc-2.24 fw8344g7xrmf7bp248xqqkncda3i26s6-hello-2.10\nStorePath: /opt/ns/nix/store/fw8344g7xrmf7bp248xqqkncda3i26s6-hello-2.10\nNarSize: 197648\n'

# narinfo = NarInfo.from_string(raw)

# print(narinfo.to_string())
