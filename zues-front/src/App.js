import React, { useEffect, useState } from 'react';
import { ChevronRight, ChevronDown, Plus, Loader, Image as ImageIcon } from 'lucide-react';
import './App.css';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = "supabaseurl";
const supabaseKey = "anonkey";

export const supabase = createClient(supabaseUrl, supabaseKey);

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTasks, setExpandedTasks] = useState({});
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    fetchTasks();
    const subscription = setupRealtimeSubscription();
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const fetchTasks = async () => {
    try {
      const { data, error } = await supabase
        .from('tasks')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setTasks(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const setupRealtimeSubscription = () => {
    return supabase
      .channel('tasks-channel')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'tasks' },
        (payload) => {
          switch (payload.eventType) {
            case 'INSERT':
              setTasks(prev => [payload.new, ...prev]);
              break;
            case 'UPDATE':
              setTasks(prev => 
                prev.map(task => 
                  task.id === payload.new.id ? payload.new : task
                )
              );
              break;
            case 'DELETE':
              setTasks(prev => 
                prev.filter(task => task.id !== payload.old.id)
              );
              break;
            default:
              break;
          }
        }
      )
      .subscribe();
  };

  const getImageUrl = (message) => {
    if (!message) return null;
    
    // Extract URL from message
    const urlMatch = message.match(/https?:\/\/[^\s]+/);
    if (!urlMatch) return null;
    
    let imageUrl = urlMatch[0];
    
    // Handle imgur URLs
    if (imageUrl.includes('imgur.com')) {
      // Remove any trailing characters or query parameters
      imageUrl = imageUrl.split(/[?\s]/)[0];
      
      // Convert to direct image URL if it's not already
      if (!imageUrl.match(/\.(jpg|jpeg|png|gif)$/i)) {
        if (imageUrl.endsWith('/')) {
          imageUrl = imageUrl.slice(0, -1);
        }
        // Convert to direct image URL
        imageUrl = imageUrl.replace('imgur.com', 'i.imgur.com');
        imageUrl = `${imageUrl}.jpg`;
      }
    }
    
    return imageUrl;
  };

  const toggleTaskExpansion = (taskId) => {
    setExpandedTasks(prev => ({
      ...prev,
      [taskId]: !prev[taskId]
    }));
  };

  const toggleTaskStatus = async (taskId, currentStatus) => {
    const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    try {
      const { error } = await supabase
        .from('tasks')
        .update({ status: newStatus })
        .eq('id', taskId);
      
      if (error) throw error;
    } catch (err) {
      console.error('Error updating task status:', err);
    }
  };

  const createNewTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    try {
      const { error } = await supabase
        .from('tasks')
        .insert([
          {
            title: newTaskTitle,
            status: 'pending'
          }
        ]);

      if (error) throw error;
      setNewTaskTitle('');
    } catch (err) {
      console.error('Error creating task:', err);
    }
  };

  if (loading) {
    return (
      <div className="loader-container">
        <Loader className="loader" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-message">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Tasks</h1>
        </header>

        <form className="new-task-form" onSubmit={createNewTask}>
          <button type="submit" className="add-task-button">
            <Plus size={16} />
          </button>
          <input
            type="text"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            placeholder="New task..."
            className="new-task-input"
          />
        </form>

        <div className="tasks-list">
          {tasks.map((task) => {
            const imageUrl = getImageUrl(task.agent_message);
            return (
              <div key={task.id} className="task-item">
                <div className="task-header">
                  <button
                    className="expand-button"
                    onClick={() => toggleTaskExpansion(task.id)}
                  >
                    {expandedTasks[task.id] ? (
                      <ChevronDown size={16} />
                    ) : (
                      <ChevronRight size={16} />
                    )}
                  </button>
                  <label className="checkbox-container">
                    <input
                      type="checkbox"
                      checked={task.status === 'completed'}
                      onChange={() => toggleTaskStatus(task.id, task.status)}
                    />
                    <span className="checkmark"></span>
                  </label>
                  <span className={`task-title ${task.status === 'completed' ? 'completed' : ''}`}>
                    {task.title}
                  </span>
                  {imageUrl && (
                    <ImageIcon size={16} className="image-indicator" />
                  )}
                </div>
                
                {expandedTasks[task.id] && (
                  <div className="task-details">
                    {task.description && (
                      <p className="task-description">{task.description}</p>
                    )}
                    {imageUrl && (
                      <div className="task-image-container">
                        <img
                          src={imageUrl}
                          alt="Task completion"
                          className="task-image"
                          onClick={() => setSelectedImage(imageUrl)}
                          loading="lazy"
                        />
                      </div>
                    )}
                    <div className="task-metadata">
                      Created: {new Date(task.created_at).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {selectedImage && (
        <div className="image-modal" onClick={() => setSelectedImage(null)}>
          <div className="modal-content">
            <img src={selectedImage} alt="Enlarged view" />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;