import React, { useState, useRef } from 'react';
import { Play, Pause, Settings, Volume2, Mic, Download, Save } from 'lucide-react';

interface VoiceSettings {
  voiceId: string;
  name: string;
  language: string;
  gender: 'female' | 'male';
  age: 'young' | 'adult' | 'mature';
  speed: number;
  pitch: number;
  volume: number;
}

interface VoiceProps {
  data: {
    character: { id: string };
  };
}

const Voice: React.FC<VoiceProps> = ({ data }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentVoice, setCurrentVoice] = useState<VoiceSettings>({
    voiceId: 'eva_voice_1',
    name: 'Ева - Стандартный',
    language: 'ru-RU',
    gender: 'female',
    age: 'young',
    speed: 1.0,
    pitch: 1.0,
    volume: 0.8
  });

  const [testText, setTestText] = useState('Привет! Это тестовое сообщение от Евы. Как тебе мой голос?');
  const [availableVoices] = useState<VoiceSettings[]>([
    {
      voiceId: 'eva_voice_1',
      name: 'Ева - Стандартный',
      language: 'ru-RU',
      gender: 'female',
      age: 'young',
      speed: 1.0,
      pitch: 1.0,
      volume: 0.8
    },
    {
      voiceId: 'eva_voice_2',
      name: 'Ева - Нежный',
      language: 'ru-RU',
      gender: 'female',
      age: 'young',
      speed: 0.9,
      pitch: 1.1,
      volume: 0.7
    },
    {
      voiceId: 'eva_voice_3',
      name: 'Ева - Игривый',
      language: 'ru-RU',
      gender: 'female',
      age: 'young',
      speed: 1.1,
      pitch: 1.2,
      volume: 0.9
    }
  ]);

  const audioRef = useRef<HTMLAudioElement>(null);

  const handleVoiceChange = (voiceId: string) => {
    const selectedVoice = availableVoices.find(v => v.voiceId === voiceId);
    if (selectedVoice) {
      setCurrentVoice(selectedVoice);
    }
  };

  const handleSettingChange = (setting: keyof VoiceSettings, value: number | string) => {
    setCurrentVoice(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  const handlePlayTest = () => {
    // Simulate TTS playback
    setIsPlaying(true);
    setTimeout(() => {
      setIsPlaying(false);
    }, 3000);
  };

  const handleStopTest = () => {
    setIsPlaying(false);
  };

  const handleSaveSettings = () => {
    // Save voice settings to backend
    console.log('Saving voice settings:', currentVoice);
    alert('Настройки голоса сохранены!');
  };

  const handleExportVoice = () => {
    // Export voice settings as JSON
    const voiceData = JSON.stringify(currentVoice, null, 2);
    const blob = new Blob([voiceData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-settings-${currentVoice.voiceId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Голос персонажа</h2>
        <p className="text-gray-600">Настройка параметров синтеза речи и голосовых характеристик</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Voice Selection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Mic size={20} />
            Выбор голоса
          </h3>
          <div className="space-y-3">
            {availableVoices.map(voice => (
              <div key={voice.voiceId} className="flex items-center">
                <input
                  type="radio"
                  id={voice.voiceId}
                  name="voice"
                  value={voice.voiceId}
                  checked={currentVoice.voiceId === voice.voiceId}
                  onChange={(e) => handleVoiceChange(e.target.value)}
                  className="mr-3"
                />
                <label htmlFor={voice.voiceId} className="flex-1 cursor-pointer">
                  <div className="font-medium text-gray-800">{voice.name}</div>
                  <div className="text-sm text-gray-500">
                    {voice.gender === 'female' ? 'Женский' : 'Мужской'} • {voice.age === 'young' ? 'Молодой' : voice.age === 'adult' ? 'Взрослый' : 'Зрелый'} • {voice.language}
                  </div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Voice Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Settings size={20} />
            Параметры голоса
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Скорость речи: {currentVoice.speed}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={currentVoice.speed}
                onChange={(e) => handleSettingChange('speed', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Медленно</span>
                <span>Быстро</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Высота тона: {currentVoice.pitch}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={currentVoice.pitch}
                onChange={(e) => handleSettingChange('pitch', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Низкий</span>
                <span>Высокий</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Громкость: {Math.round(currentVoice.volume * 100)}%
              </label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={currentVoice.volume}
                onChange={(e) => handleSettingChange('volume', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Тихо</span>
                <span>Громко</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Test Voice */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Volume2 size={20} />
          Тест голоса
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тестовый текст
            </label>
            <textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24 resize-none"
              placeholder="Введите текст для тестирования голоса..."
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={isPlaying ? handleStopTest : handlePlayTest}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                isPlaying 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              {isPlaying ? 'Остановить' : 'Проиграть'}
            </button>
            <button
              onClick={handleSaveSettings}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Save size={16} />
              Сохранить настройки
            </button>
            <button
              onClick={handleExportVoice}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Download size={16} />
              Экспорт
            </button>
          </div>
          {isPlaying && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="animate-pulse bg-blue-600 rounded-full w-3 h-3"></div>
                <span className="text-blue-800 font-medium">Воспроизведение...</span>
              </div>
              <div className="mt-2">
                <div className="bg-blue-200 rounded-full h-2 animate-pulse"></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Voice Info */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Информация о голосе</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{currentVoice.speed}x</div>
            <div className="text-sm text-gray-500">Скорость</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{currentVoice.pitch}x</div>
            <div className="text-sm text-gray-500">Высота</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{Math.round(currentVoice.volume * 100)}%</div>
            <div className="text-sm text-gray-500">Громкость</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{currentVoice.language}</div>
            <div className="text-sm text-gray-500">Язык</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Voice;