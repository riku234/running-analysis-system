# ==========================================
# ルールベースアドバイスマスタデータ（自動生成版）
# ==========================================
# このファイルは、Z値に基づくルールベース診断のマスタデータを定義します。

ADVICE_MASTER_DATA = {
    "ISSUE_TRUNK_BACKWARD": {
        "rule": {
            "target_event": None,  # 全イベントをチェック
            "target_metric": "trunk_angle_z",
            "operator": "lt",
            "threshold": -1.5,
            "severity": "high"
        },
        "content": {
            "name": "腰落ち（後傾）フォーム",
            "observation": "重心が後ろに残り、ブレーキがかかっています。脚の筋肉への負担が大きい走り方です。",
            "cause": "骨盤が後傾しており、着地時にお尻が落ちてしまっています。",
            "action": "おへそからロープで前に引っ張られるようなイメージを持ち、自然な前傾姿勢を作りましょう。",
            "drill": {
                "name": "ウォールドリル（壁押し）",
                "url": "https://youtube.com/example_wall_drill"
            }
        }
    },
    "ISSUE_TRUNK_FORWARD": {
        "rule": {
            "target_event": None,
            "target_metric": "trunk_angle_z",
            "operator": "gt",
            "threshold": 1.5,
            "severity": "high"
        },
        "content": {
            "name": "突っ込み（前傾過多）",
            "observation": "上半身が前に倒れすぎており、足の回転が追いついていません。",
            "cause": "股関節からの前傾ではなく、腰から上が折れ曲がっている状態です。",
            "action": "頭のてっぺんを空から吊るされている意識を持ち、背筋を伸ばしたまま前傾しましょう。",
            "drill": {
                "name": "トロッティング（小走り）",
                "url": "https://youtube.com/example_trotting"
            }
        }
    },
    "ISSUE_OVERSTRIDE": {
        "rule": {
            "target_event": None,
            "target_metric": "shank_angle_z",
            "operator": "gt",
            "threshold": 1.5,
            "severity": "high"
        },
        "content": {
            "name": "オーバーストライド",
            "observation": "着地位置が体の重心よりもかなり前方にあります。強いブレーキがかかっています。",
            "cause": "歩幅を無理に広げようとして、膝下が前に振り出されすぎています。",
            "action": "足音を小さくするイメージで、体の真下に着地することを意識しましょう。",
            "drill": {
                "name": "もも上げドリル",
                "url": "https://youtube.com/example_high_knees"
            }
        }
    },
    "ISSUE_KNEE_COLLAPSE": {
        "rule": {
            "target_event": None,
            "target_metric": "knee_angle_z",
            "operator": "gt",
            "threshold": 1.5,
            "severity": "medium"
        },
        "content": {
            "name": "膝の沈み込み",
            "observation": "着地した瞬間に膝が深く曲がりすぎています。",
            "cause": "着地の衝撃を筋肉だけで受け止めており、バネを使えていません。",
            "action": "地面からの反発をもらう感覚を養い、接地時間を短くしましょう。",
            "drill": {
                "name": "アンクルホップ（縄跳び）",
                "url": "https://youtube.com/example_ankle_hop"
            }
        }
    },
    "ISSUE_THIGH_ANGLE_LOW": {
        "rule": {
            "target_event": None,
            "target_metric": "thigh_angle_z",
            "operator": "lt",
            "threshold": -1.5,
            "severity": "medium"
        },
        "content": {
            "name": "足の還り（遅れ）",
            "observation": "蹴り出した足が後ろに流れ、次の一歩が出るのが遅れています。",
            "cause": "腸腰筋（足を引き上げる筋肉）がうまく使えておらず、足だけで走っています。",
            "action": "踵をお尻に素早く引きつける「折りたたみ」の動作を意識しましょう。",
            "drill": {
                "name": "踵タッチ（バットキック）",
                "url": "https://youtube.com/example_heel_touch"
            }
        }
    }
}

