import React, { useState, useEffect } from 'react';
import axios from 'axios';
import useAuthStore from '../store/useAuthStore';
import WorkflowModal from '../components/Comfy/WorkflowModal';

const API_URL = '';

interface ComfyWorkflow {
  id: string;
  name: string;
  description: string;
  workflow_data: object;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const ComfyWorkflows: React.FC = () => {
  const [workflows, setWorkflows] = useState<ComfyWorkflow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<ComfyWorkflow | null>(null);
  const { token } = useAuthStore();

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_URL}/admin/comfy-workflows/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (Array.isArray(response.data)) {
        setWorkflows(response.data);
      } else {
        console.error('Expected an array of workflows, but received:', response.data);
        setWorkflows([]); // Reset to empty array to prevent crash
        setError('Received unexpected data format from the server.');
      }
    } catch (err) {
      setError('Failed to fetch workflows.');
      console.error(err);
      setWorkflows([]); // Reset to empty array on error to prevent crash
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenModal = (workflow: ComfyWorkflow | null = null) => {
    setSelectedWorkflow(workflow);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedWorkflow(null);
  };

  const handleSaveWorkflow = async (workflowData: any) => {
    if (!workflowData.name || !workflowData.workflow_data) {
      setError('Name and workflow data are required.');
      return;
    }

    const method = selectedWorkflow ? 'put' : 'post';
    const url = selectedWorkflow
      ? `${API_URL}/admin/comfy-workflows/${selectedWorkflow.id}`
      : `${API_URL}/admin/comfy-workflows/`;

    try {
      await axios[method](url, workflowData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      handleCloseModal();
      fetchWorkflows();
    } catch (err: any) {
      if (err.response && err.response.status === 409) {
        setError(err.response.data.detail);
      } else {
        setError(`Failed to save workflow.`);
      }
      console.error(err);
    }
  };

  const handleSetActive = async (workflowId: string) => {
    try {
      await axios.post(`${API_URL}/admin/comfy-workflows/${workflowId}/set-active`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchWorkflows(); // Refresh list to show the new active status
    } catch (err) {
      setError('Failed to set workflow active.');
      console.error(err);
    }
  };

  const handleDelete = async (workflowId: string) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      try {
        await axios.delete(`${API_URL}/admin/comfy-workflows/${workflowId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        });
        fetchWorkflows();
      } catch (err) {
        setError('Failed to delete workflow. Make sure it is not active.');
        console.error(err);
      }
    }
  };


  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">ComfyUI Workflows</h1>
        <button 
          onClick={() => handleOpenModal()}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          Add New Workflow
        </button>
      </div>
      
      {isLoading && <p>Loading workflows...</p>}
      {error && <p className="text-red-500">{error}</p>}
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full leading-normal">
          <thead>
            <tr>
              <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
              <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Description</th>
              <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
              <th className="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            {workflows.map((wf) => (
              <tr key={wf.id}>
                <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                  <p className="text-gray-900 whitespace-no-wrap">{wf.name}</p>
                </td>
                <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                  <p className="text-gray-900 whitespace-no-wrap">{wf.description}</p>
                </td>
                <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                  <span className={`relative inline-block px-3 py-1 font-semibold leading-tight ${wf.is_active ? 'text-green-900' : 'text-gray-700'}`}>
                    <span aria-hidden className={`absolute inset-0 ${wf.is_active ? 'bg-green-200' : 'bg-gray-200'} opacity-50 rounded-full`}></span>
                    <span className="relative">{wf.is_active ? 'Active' : 'Inactive'}</span>
                  </span>
                </td>
                <td className="px-5 py-5 border-b border-gray-200 bg-white text-sm">
                  <button onClick={() => handleOpenModal(wf)} className="text-indigo-600 hover:text-indigo-900 mr-4">Edit</button>
                  {!wf.is_active && (
                     <button onClick={() => handleSetActive(wf.id)} className="text-green-600 hover:text-green-900 mr-4">Set Active</button>
                  )}
                  <button onClick={() => handleDelete(wf.id)} className="text-red-600 hover:text-red-900">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <WorkflowModal 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveWorkflow}
        workflow={selectedWorkflow}
      />
    </div>
  );
};

export default ComfyWorkflows;
