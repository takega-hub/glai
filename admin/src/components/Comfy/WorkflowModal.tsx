import React, { useState, useEffect } from 'react';

interface WorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (workflow: any) => void;
  workflow: any | null;
}

const WorkflowModal: React.FC<WorkflowModalProps> = ({ isOpen, onClose, onSave, workflow }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [workflowData, setWorkflowData] = useState('');

  useEffect(() => {
    if (workflow) {
      setName(workflow.name);
      setDescription(workflow.description);
      setWorkflowData(JSON.stringify(workflow.workflow_data, null, 2));
    } else {
      setName('');
      setDescription('');
      setWorkflowData('');
    }
  }, [workflow, isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    try {
      const parsedData = JSON.parse(workflowData);
      onSave({ name, description, workflow_data: parsedData });
    } catch (e) {
      alert('Invalid JSON in workflow data!');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
        <h2 className="text-xl font-bold mb-4">{workflow ? 'Edit Workflow' : 'Add New Workflow'}</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Workflow Data (JSON)</label>
            <textarea
              value={workflowData}
              onChange={(e) => setWorkflowData(e.target.value)}
              rows={15}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm font-mono"
            />
          </div>
        </div>
        <div className="mt-6 flex justify-end space-x-2">
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">Cancel</button>
          <button onClick={handleSave} className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">Save</button>
        </div>
      </div>
    </div>
  );
};

export default WorkflowModal;
