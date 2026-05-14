#!/bin/bash

# Thin wrapper for scripts/setup.sh
exec bash "$(dirname "$0")/scripts/setup.sh" "$@"
