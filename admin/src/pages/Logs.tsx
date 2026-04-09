import React from 'react';

const Logs: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Логи действий и чатов</h1>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <p>Раздел для просмотра логов действий администраторов и модерации чатов пользователей.</p>
        <p className="mt-4 text-gray-500">Этот раздел находится в разработке.</p>
      </div>
    </div>
  );
};

export default Logs;
