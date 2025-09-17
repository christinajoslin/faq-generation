#!/bin/bash

echo "program starting"

python _1_clean_tickets/clean_tickets_tdx.py False
echo "tdx tickets cleaned"

python _1_clean_tickets/clean_tickets_anvil.py False
echo "anvil tickets cleaned"

echo "all tickets cleaned"
