# config.py

# Enable Flask's debugging features. Should be False in production
DEBUG = True
DEBUG = False

# To generate another key, use the following python code:
# 	>>>import os
# 	>>>os.urandom(24).hex()
# Source: https://gist.github.com/geoffalday/2021517

secret_key = 'f47814c97183c13d1896682174b2778962aaf09e4d10617a'