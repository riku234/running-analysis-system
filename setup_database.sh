#!/bin/bash

# データベース接続情報
DB_HOST="running-analysis-db.cluster-cbqqcwic00jv.ap-southeast-2.rds.amazonaws.com"
DB_PORT="5432"
DB_NAME="running-analysis-db"
DB_USER="postgres"

echo "================================================"
echo "データベーステーブル作成スクリプト"
echo "================================================"
echo ""
echo "接続先: $DB_HOST"
echo "データベース: $DB_NAME"
echo ""
echo "⚠️  パスワードの入力が必要です"
echo ""

# psqlコマンドでテーブルを作成
PGPASSWORD="vfmdev_01" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database_schema.sql

echo ""
echo "================================================"
echo "完了！"
echo "================================================"
