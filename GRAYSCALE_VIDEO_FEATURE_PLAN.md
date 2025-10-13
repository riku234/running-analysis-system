# 動画グレースケール機能 - 実装計画

## 📋 概要

**目的**: 結果ページの動画解析カードで動画をグレースケール表示し、キーポイント（骨格線）を視覚的に目立たせる

**要件**:
- ✅ いつでも元に戻せるようにトグル機能を実装
- ✅ ユーザーが簡単に切り替えられるUI
- ✅ キーポイント表示との組み合わせで視認性向上

---

## 🎯 実装方式の選択肢

### オプション1: CSS フィルター（推奨）

**実装方法**:
```css
.grayscale-video {
  filter: grayscale(100%);
}
```

**メリット**:
- ✅ 実装が非常に簡単（CSSのみ）
- ✅ パフォーマンスが良い（GPU加速）
- ✅ 動画ファイルは変更不要
- ✅ リアルタイムで切り替え可能
- ✅ ブラウザのネイティブ機能を使用

**デメリット**:
- ⚠️ 古いブラウザでは非対応（IE11以下）
- ⚠️ 動画のみグレースケール（キーポイントはそのまま）

**推奨度**: ⭐⭐⭐⭐⭐（最推奨）

---

### オプション2: Canvas + 画像処理

**実装方法**:
- 動画を`<canvas>`で再生
- フレームごとにグレースケール変換
- キーポイントを描画

**メリット**:
- ✅ 完全なカスタマイズが可能
- ✅ 動画とキーポイントを一緒に処理可能

**デメリット**:
- ❌ 実装が複雑
- ❌ パフォーマンスが低い（CPU負荷が高い）
- ❌ 動画コントロール（再生/一時停止）を自前で実装
- ❌ 開発・メンテナンスコストが高い

**推奨度**: ⭐⭐☆☆☆（非推奨）

---

### オプション3: バックエンドで動画変換

**実装方法**:
- アップロード時にグレースケール動画を生成
- 2つのバージョン（カラー/グレースケール）を保存

**メリット**:
- ✅ クライアント側の処理不要

**デメリット**:
- ❌ ストレージ容量が2倍
- ❌ 変換処理時間がかかる
- ❌ 既存動画の再処理が必要
- ❌ リアルタイム切り替えができない

**推奨度**: ⭐☆☆☆☆（非推奨）

---

## 🏗️ 推奨実装: オプション1（CSSフィルター）

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│ 結果ページ (frontend/app/result/[id]/page.tsx)         │
│                                                         │
│  1. グレースケールトグル状態を追加                      │
│     const [isGrayscale, setIsGrayscale] = useState(false)│
│                                                         │
│  2. トグルボタンを追加                                  │
│     「🎨 カラー / ⚫ グレースケール」                  │
│                                                         │
│  3. 動画タグにCSS classを動的に適用                     │
│     className={isGrayscale ? 'grayscale-video' : ''}   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 実装詳細

### Phase 1: 状態管理の追加

**ファイル**: `frontend/app/result/[id]/page.tsx`

```typescript
// 状態管理に追加
const [isGrayscale, setIsGrayscale] = useState(false)
```

---

### Phase 2: CSSスタイルの追加

**ファイル**: `frontend/app/result/[id]/page.tsx`（同じファイル内にスタイル定義）

または

**ファイル**: `frontend/app/globals.css`

```css
/* グレースケールフィルター */
.grayscale-video {
  filter: grayscale(100%);
  transition: filter 0.3s ease; /* スムーズな切り替え */
}

/* オプション: コントラストを少し上げて見やすく */
.grayscale-video-enhanced {
  filter: grayscale(100%) contrast(1.1) brightness(1.05);
  transition: filter 0.3s ease;
}
```

---

### Phase 3: トグルボタンUIの追加

**ファイル**: `frontend/app/result/[id]/page.tsx`

**配置場所**: 動画プレイヤーの上部または下部

```tsx
{/* グレースケールトグルボタン */}
<div className="flex items-center justify-between mb-2">
  <h3 className="text-lg font-semibold">動画解析</h3>
  <Button
    onClick={() => setIsGrayscale(!isGrayscale)}
    variant="outline"
    size="sm"
    className="flex items-center gap-2"
  >
    {isGrayscale ? (
      <>
        <span className="text-gray-600">⚫</span>
        グレースケール
      </>
    ) : (
      <>
        <span className="text-blue-600">🎨</span>
        カラー
      </>
    )}
  </Button>
</div>
```

---

### Phase 4: 動画タグへのクラス適用

**ファイル**: `frontend/app/result/[id]/page.tsx`

**現在の動画タグ**:
```tsx
<video
  ref={videoRef}
  className="w-full rounded-lg shadow-md"
  controls
  playsInline
  onTimeUpdate={handleTimeUpdate}
  onLoadedMetadata={handleLoadedMetadata}
>
  <source src={videoUrl} type="video/mp4" />
</video>
```

**修正後**:
```tsx
<video
  ref={videoRef}
  className={`w-full rounded-lg shadow-md ${isGrayscale ? 'grayscale-video' : ''}`}
  controls
  playsInline
  onTimeUpdate={handleTimeUpdate}
  onLoadedMetadata={handleLoadedMetadata}
>
  <source src={videoUrl} type="video/mp4" />
</video>
```

---

## 🎨 UI デザイン案

### オプションA: シンプルなトグルボタン

```
┌────────────────────────────────────────┐
│ 動画解析            [🎨 カラー ▼]     │
├────────────────────────────────────────┤
│                                        │
│        [動画プレイヤー]                │
│                                        │
└────────────────────────────────────────┘
```

### オプションB: スイッチスタイル

```
┌────────────────────────────────────────┐
│ 動画解析                               │
│ 表示モード: [🎨カラー | ⚫グレー]      │
├────────────────────────────────────────┤
│                                        │
│        [動画プレイヤー]                │
│                                        │
└────────────────────────────────────────┘
```

### オプションC: ドロップダウン（将来の拡張性）

```
┌────────────────────────────────────────┐
│ 動画解析        [表示フィルター ▼]    │
│                 ┌─────────────────┐    │
│                 │ ✓ カラー        │    │
│                 │   グレースケール│    │
│                 │   高コントラスト│    │
│                 └─────────────────┘    │
├────────────────────────────────────────┤
```

**推奨**: オプションA（シンプルで直感的）

---

## 🔄 元に戻す方法

### 方法1: Gitで管理（推奨）

```bash
# 現在の状態をコミット
git add frontend/app/result/[id]/page.tsx
git commit -m "feat: 動画グレースケール表示機能を追加"

# 元に戻す場合
git revert HEAD
# または
git reset --hard HEAD~1  # ローカルのみの場合
```

### 方法2: フィーチャーフラグ

**実装例**:
```typescript
// 設定ファイルまたは環境変数で制御
const ENABLE_GRAYSCALE_FEATURE = process.env.NEXT_PUBLIC_ENABLE_GRAYSCALE === 'true'

// UIで条件分岐
{ENABLE_GRAYSCALE_FEATURE && (
  <Button onClick={() => setIsGrayscale(!isGrayscale)}>
    グレースケール切替
  </Button>
)}
```

### 方法3: ブランチ管理

```bash
# 機能ブランチで開発
git checkout -b feature/grayscale-video

# 本番には反映せず、テスト環境のみ
# 気に入らなければブランチを削除
git branch -D feature/grayscale-video
```

---

## 📊 実装スケジュール

| フェーズ | タスク | 所要時間 | 優先度 |
|---------|--------|---------|--------|
| **Phase 1** | 状態管理追加 | 5分 | 高 |
| **Phase 2** | CSSスタイル追加 | 5分 | 高 |
| **Phase 3** | トグルボタンUI | 15分 | 高 |
| **Phase 4** | 動画タグ修正 | 5分 | 高 |
| **テスト** | ローカル確認 | 10分 | 高 |
| **デプロイ** | EC2反映 | 5分 | 中 |

**合計所要時間**: 約45分

---

## ✅ テストシナリオ

### 1. 正常系

1. ✅ トグルボタンをクリックで動画がグレースケールになる
2. ✅ 再度クリックでカラーに戻る
3. ✅ キーポイント表示との併用でキーポイントが目立つ
4. ✅ 動画の再生/一時停止/シークが正常に動作

### 2. UIテスト

1. ✅ ボタンが適切な位置に配置される
2. ✅ モバイルでも正しく表示される
3. ✅ 状態（カラー/グレー）が視覚的に分かる

### 3. パフォーマンステスト

1. ✅ 切り替えがスムーズ（ラグなし）
2. ✅ 動画再生に影響なし

---

## 🎯 期待される効果

### 視認性向上

**Before（カラー）**:
- 動画のカラー情報とキーポイントの色が混在
- 背景の色によってはキーポイントが見づらい

**After（グレースケール）**:
- 動画がモノトーンになり、キーポイントの色が際立つ
- 骨格線の動きに集中しやすい
- フォーム分析により適した表示

### 使用シーン

1. **詳細分析時**: グレースケールで骨格に集中
2. **全体確認時**: カラーで自然な動画確認
3. **比較時**: 2つのモードを切り替えて確認

---

## 🔧 将来の拡張案

### オプション1: 複数フィルター

```typescript
type VideoFilter = 'normal' | 'grayscale' | 'high-contrast' | 'sepia'

const filters = {
  normal: '',
  grayscale: 'grayscale(100%)',
  'high-contrast': 'grayscale(100%) contrast(1.3) brightness(1.1)',
  sepia: 'sepia(60%)'
}
```

### オプション2: キーポイント色の自動調整

グレースケール時にキーポイントの色を変更して、さらに目立たせる

### オプション3: ユーザー設定の保存

```typescript
// localStorageに保存
localStorage.setItem('videoDisplayMode', 'grayscale')
```

---

## 📝 まとめ

**推奨実装方式**: CSSフィルター（オプション1）

**理由**:
- ✅ 実装が簡単（約45分）
- ✅ パフォーマンスが良い
- ✅ いつでも元に戻せる
- ✅ ユーザーが自由に切り替え可能

**元に戻す方法**: Gitのrevertまたはreset

**実装開始の準備ができたら、お知らせください！**

---

## 🚀 実装コマンド（参考）

```bash
# フィーチャーブランチ作成（オプション）
git checkout -b feature/grayscale-video

# 実装後
git add frontend/app/result/[id]/page.tsx
git commit -m "feat: 動画グレースケール表示機能を追加（トグル可能）"

# テスト後、気に入ったらmainにマージ
git checkout main
git merge feature/grayscale-video

# 気に入らなければブランチ削除
git branch -D feature/grayscale-video
```

