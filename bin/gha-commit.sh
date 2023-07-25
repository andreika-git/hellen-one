#!/bin/bash
git config --local user.email "action@github.com"
git config --local user.name "GitHub create-board Action"
git add gerber/*
git add boards/*
git reset HEAD *.kicad_pro
git status
OUT=$(git commit -am "[skip actions] Auto-generated board" 2>&1) || echo "commit failed, finding out why"
if echo "$OUT" | grep 'nothing to commit' || echo "$OUT" | grep 'nothing added to commit'; then
  echo "headers: looks like nothing to commit"
  echo "::set-env name=NOCOMMIT::true"
  exit 0
elif echo "$OUT" | grep 'changed'; then
  echo "headers: looks like something has changed"
  exit 0
else
  echo "headers: looks like something unexpected"
  exit 1
fi

