#!/bin/sh
openssl aes-256-cbc -K $encrypted_aa5263036386_key -iv $encrypted_aa5263036386_iv -in .travis/ssh_key.enc -out .travis/deploy -d
echo "madoka.whs.in.th,103.246.18.42 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDN717hGRfIpN9psGG9q8VXuyVE6w8H1Fa0BqkHOBGJFgAq2uV0/bdYNOpvG27ngLDOmOmNLpdlIYQiI56E+qUPUBxLH3fvhVQVKItP5MRlc97an98Ozg+bOl3SjdUWgFeHIRHwu6UllZUL8U6pjJS/GZsumzwwwTOnLRutYWegxeHjW2DU5Q2BkCU5z/3b+7gFu4s9gRFZ57En/GG2aZYrKBGgoUvjEAOL3B+/nCm1ZTlV2IdKA9gpF/7SyZIozKHXXUA/Xw27aOxebFL2VHO7YtgvkNoiJ5uc6ZQuRB9VPmNKBSYH5fwSICtSHTGlCKLOUd91SBG8JRm/fXES24jn" > $HOME/.ssh/known_hosts
chmod 600 .travis/deploy $HOME/.ssh/known_hosts
ssh -i .travis/deploy vu2003@madoka.whs.in.th social/deploy.sh