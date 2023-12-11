#!/bin/bash
git config --local user.email "action@github.com"
git config --local user.name "GitHub create-board Action v2"
echo "Status 1/3"
git status
git restore *.kicad_pro
echo "Status 2/3"
git status
git add gerber/*
git add boards/*
echo "Status 3/3"
git status
OUT=$(git commit -am "[skip actions] Auto-generated board" 2>&1) || echo "commit failed, finding out why"
if echo "$OUT" | grep 'nothing to commit' || echo "$OUT" | grep 'nothing added to commit'; then
  echo "headers: looks like nothing to commit"
# todo: NOCOMMIT is deprecated I guess? YESCOMMIT works better with multiple invocations per action
  echo "::set-env name=NOCOMMIT::true"
  exit 0
elif echo "$OUT" | grep 'changed'; then
  echo "headers: looks like something has changed"
  echo "::set-env name=YESCOMMIT::true"
  exit 0
else
  echo "headers: looks like something unexpected"
  exit 1
fi

