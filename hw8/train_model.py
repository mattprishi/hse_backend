#!/usr/bin/env python3
"""Обучение и сохранение модели (отдельно от API/воркера). Запуск из каталога hw8:
   python train_model.py [path_to_pkl]
"""
from __future__ import annotations

import sys

from config import MODEL_PATH
from ml.model import save_model, train_model


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else MODEL_PATH
    model = train_model()
    save_model(model, path)
    print(f"Model trained and saved to {path}")


if __name__ == "__main__":
    main()
