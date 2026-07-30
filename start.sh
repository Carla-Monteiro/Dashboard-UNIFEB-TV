#!/bin/bash

# 🚀 SCRIPT QUE RODA BACKEND + SINCRONIZAÇÃO NO RENDER

echo "🚀 INICIANDO UNIFEB BACKEND + SINCRONIZAÇÃO"
echo "==========================================="
echo ""

# Iniciar sincronização em background
echo "1️⃣  Iniciando sincronização contínua..."
python sync_loop.py &
SYNC_PID=$!

sleep 2

# Iniciar backend em foreground
echo ""
echo "2️⃣  Iniciando backend Flask..."
echo ""

python form_handler.py
