#!/bin/bash
export N8N_USER_FOLDER="$(pwd)/n8n_data"
export N8N_SECURE_COOKIE=false
npx n8n
