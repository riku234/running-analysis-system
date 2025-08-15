import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// 骨格データの型定義
interface PoseKeypoint {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

interface PoseFrame {
  frame_number: number;
  timestamp: number;
  keypoints: PoseKeypoint[];
  landmarks_detected: boolean;
}

// ストア状態の型定義
interface ResultState {
  // 骨格データ（巨大なデータ）
  poseData: PoseFrame[] | null;
  
  // 動画情報
  videoInfo: {
    fps: number;
    total_frames: number;
    duration_seconds: number;
    width: number;
    height: number;
  } | null;
  
  // アップロード情報
  uploadInfo: {
    file_id: string;
    original_filename: string;
    saved_filename: string;
    file_size: number;
    content_type: string;
    upload_timestamp: string;
    file_extension: string;
  } | null;

  // アクション
  setPoseData: (data: PoseFrame[]) => void;
  setVideoInfo: (info: any) => void;
  setUploadInfo: (info: any) => void;
  clearData: () => void;
}

// Zustandストアの作成（永続化付き）
export const useResultStore = create<ResultState>()(
  persist(
    (set) => ({
      // 初期状態
      poseData: null,
      videoInfo: null,
      uploadInfo: null,
      
      // アクション
      setPoseData: (data) => set({ poseData: data }),
      setVideoInfo: (info) => set({ videoInfo: info }),
      setUploadInfo: (info) => set({ uploadInfo: info }),
      clearData: () => set({ 
        poseData: null, 
        videoInfo: null, 
        uploadInfo: null 
      }),
    }),
    {
      name: 'result-storage', // localStorage のキー名
      // 大きなデータなので sessionStorage を使用（タブを閉じると削除）
      storage: {
        getItem: (name) => {
          const item = sessionStorage.getItem(name);
          return item ? JSON.parse(item) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
    }
  )
); 