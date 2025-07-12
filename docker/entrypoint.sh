#!/bin/bash

source /app/backend/.venv/bin/activate
export PATH=$HOME/.bun/bin:$PATH
exec $@
