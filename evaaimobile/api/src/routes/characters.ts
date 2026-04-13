import express from 'express';
import multer from 'multer';
import fs from 'fs';
import path from 'path';

const router = express.Router();

// Настройка multer для сохранения файлов
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadPath = path.join(__dirname, '../../public/characters', req.params.id);
    // Создаем папку для персонажа, если она не существует
    fs.mkdirSync(uploadPath, { recursive: true });
    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    // Используем уникальное имя файла, чтобы избежать конфликтов
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });

// Эндпоинт для загрузки аватара
router.post('/:id/upload', upload.single('avatar'), (req, res) => {
  if (!req.file) {
    return res.status(400).send({ message: 'Файл не был загружен.' });
  }

  // Формируем путь к файлу, который будет доступен из веба
  const filePath = `/characters/${req.params.id}/${req.file.filename}`;

  res.status(200).send({ filePath: filePath });
});

export default router;
