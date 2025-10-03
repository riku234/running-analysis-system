#!/bin/bash

echo "================================================"
echo "データベース接続テスト"
echo "================================================"
echo ""
echo "接続情報:"
echo "  ホスト: running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com"
echo "  ポート: 5432"
echo "  データベース: running-analysis-db"
echo ""
echo "Dockerコンテナから接続テスト中..."
echo ""

docker compose run --rm video_processing python3 db_utils.py

echo ""
echo "================================================"
