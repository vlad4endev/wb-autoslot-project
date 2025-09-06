import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx';
import { useAuth } from '../contexts/AuthContext';
import { 
  Play, 
  Pause, 
  Trash2, 
  Plus, 
  Settings, 
  User, 
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  Info
} from 'lucide-react';
import WBAccountModal from './WBAccountModal';
import CreateTaskModal from './CreateTaskModal';

const Dashboard = () => {
  const { user, logout, apiCall } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [events, setEvents] = useState([]);
  const [wbAccounts, setWbAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showWBModal, setShowWBModal] = useState(false);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchData();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchData();
    }, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch tasks
      const tasksResponse = await apiCall('/tasks');
      if (tasksResponse.ok) {
        const tasksData = await tasksResponse.json();
        setTasks(tasksData.tasks || []);
      }

      // Fetch events
      const eventsResponse = await apiCall('/events');
      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        setEvents(eventsData.events || []);
      }

      // Fetch WB accounts
      const wbResponse = await apiCall('/wb-accounts');
      if (wbResponse.ok) {
        const wbData = await wbResponse.json();
        setWbAccounts(wbData.accounts || []);
      }

    } catch (error) {
      setError('Ошибка загрузки данных');
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setLastUpdate(new Date());
    }
  };

  const handleTaskAction = async (taskId, action) => {
    try {
      const response = await apiCall(`/tasks/${taskId}/${action}`, {
        method: 'POST'
      });

      if (response.ok) {
        fetchData(); // Refresh data
      } else {
        const data = await response.json();
        setError(data.error || `Ошибка выполнения действия: ${action}`);
      }
    } catch (error) {
      setError('Ошибка сети');
      console.error('Task action error:', error);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!confirm('Вы уверены, что хотите удалить эту задачу?')) return;

    try {
      const response = await apiCall(`/tasks/${taskId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchData(); // Refresh data
      } else {
        const data = await response.json();
        setError(data.error || 'Ошибка удаления задачи');
      }
    } catch (error) {
      setError('Ошибка сети');
      console.error('Delete task error:', error);
    }
  };

  const handleTaskCreated = (newTask) => {
    setTasks(prev => [newTask, ...prev]);
    setError('');
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { variant: 'default', text: 'Активна', icon: Play },
      paused: { variant: 'secondary', text: 'Приостановлена', icon: Pause },
      completed: { variant: 'success', text: 'Завершена', icon: CheckCircle },
      error: { variant: 'destructive', text: 'Ошибка', icon: AlertCircle }
    };

    const config = statusConfig[status] || statusConfig.active;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.text}
      </Badge>
    );
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default: return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">WB AutoSlot</h1>
            </div>
            <div className="flex items-center space-x-4">
              {lastUpdate && (
                <div className="text-xs text-gray-500">
                  Обновлено: {lastUpdate.toLocaleTimeString()}
                </div>
              )}
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user?.phone}</span>
              </div>
              <Button variant="outline" size="sm" onClick={logout}>
                Выйти
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dashboard">Дашборд</TabsTrigger>
            <TabsTrigger value="tasks">Задачи</TabsTrigger>
            <TabsTrigger value="events">События</TabsTrigger>
            <TabsTrigger value="settings">Настройки</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Активные задачи</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {tasks.filter(task => task.status === 'active').length}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    из {tasks.length} общих
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Найдено слотов</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {tasks.reduce((sum, task) => sum + (task.found_slots || 0), 0)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    всего найдено
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">WB Аккаунты</CardTitle>
                  <Settings className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{wbAccounts.length}</div>
                  <p className="text-xs text-muted-foreground">
                    подключено
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Tasks */}
            <Card>
              <CardHeader>
                <CardTitle>Последние задачи</CardTitle>
                <CardDescription>
                  Обзор ваших недавних задач поиска слотов
                </CardDescription>
              </CardHeader>
              <CardContent>
                {tasks.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">У вас пока нет задач</p>
                    <Button 
                      className="mt-4" 
                      onClick={() => setShowCreateTaskModal(true)}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Создать задачу
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {tasks.slice(0, 5).map((task) => (
                      <div key={task.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              #{task.id}
                            </span>
                            <h4 className="font-medium">{task.name}</h4>
                          </div>
                          <p className="text-sm text-gray-500 mt-1">
                            {task.warehouse} • {task.packaging} • Коэф. {task.coefficient}
                          </p>
                          <p className="text-sm text-gray-500">
                            {task.dateRange}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(task.status)}
                          {task.found_slots > 0 && (
                            <Badge variant="success">
                              {task.found_slots} слотов
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tasks Tab */}
          <TabsContent value="tasks" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Управление задачами</h2>
              <Button onClick={() => setShowCreateTaskModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Создать задачу
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                {tasks.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500 mb-4">У вас пока нет задач</p>
                    <Button onClick={() => setShowCreateTaskModal(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Создать первую задачу
                    </Button>
                  </div>
                ) : (
                  <div className="divide-y">
                    {tasks.map((task) => (
                      <div key={task.id} className="p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                #{task.id}
                              </span>
                              <h3 className="font-medium">{task.name}</h3>
                              {getStatusBadge(task.status)}
                            </div>
                            <div className="mt-2 text-sm text-gray-500">
                              <p><strong>Склад:</strong> {task.warehouse} • <strong>Упаковка:</strong> {task.packaging} • <strong>Коэффициент:</strong> {task.coefficient}</p>
                              <p><strong>Период:</strong> {task.dateRange}</p>
                              {task.lastCheck && (
                                <p className="flex items-center gap-1 mt-1">
                                  <Clock className="h-3 w-3" />
                                  Последняя проверка: {task.lastCheck}
                                </p>
                              )}
                              {task.wb_account && (
                                <p className="text-xs text-blue-600 mt-1">
                                  WB аккаунт: {task.wb_account.account_name}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {task.found_slots > 0 && (
                              <Badge variant="success">
                                {task.found_slots} слотов
                              </Badge>
                            )}
                            <div className="flex space-x-1">
                              {task.status === 'active' ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleTaskAction(task.id, 'pause')}
                                >
                                  <Pause className="h-4 w-4" />
                                </Button>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleTaskAction(task.id, 'start')}
                                >
                                  <Play className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDeleteTask(task.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Events Tab */}
          <TabsContent value="events" className="space-y-6">
            <h2 className="text-2xl font-bold">Журнал событий</h2>
            
            <Card>
              <CardContent className="p-0">
                {events.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Пока нет событий</p>
                  </div>
                ) : (
                  <div className="divide-y max-h-96 overflow-y-auto">
                    {events.map((event) => (
                      <div key={event.id} className="p-4 flex items-start space-x-3">
                        {getEventIcon(event.type)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            {event.message}
                          </p>
                          {event.task_name && (
                            <p className="text-xs text-gray-500">
                              Задача: {event.task_name}
                            </p>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {event.time}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-2xl font-bold">Настройки</h2>
            
            <Card>
              <CardHeader>
                <CardTitle>Аккаунты Wildberries</CardTitle>
                <CardDescription>
                  Управление подключенными аккаунтами WB
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {wbAccounts.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-4">У вас нет подключенных аккаунтов WB</p>
                      <Button onClick={() => setShowWBModal(true)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Подключить аккаунт WB
                      </Button>
                    </div>
                  ) : (
                    <>
                      {wbAccounts.map((account) => (
                        <div key={account.id} className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <h4 className="font-medium">{account.account_name}</h4>
                            <p className="text-sm text-gray-500">
                              Последний вход: {account.last_login || 'Никогда'}
                            </p>
                          </div>
                          <Badge variant={account.is_active ? 'default' : 'secondary'}>
                            {account.is_active ? 'Активен' : 'Неактивен'}
                          </Badge>
                        </div>
                      ))}
                      <Button onClick={() => setShowWBModal(true)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Добавить аккаунт
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* WB Account Modal */}
      {showWBModal && (
        <WBAccountModal
          isOpen={showWBModal}
          onClose={() => setShowWBModal(false)}
          onSuccess={() => {
            setShowWBModal(false);
            fetchData();
          }}
        />
      )}

      {/* Create Task Modal */}
      <CreateTaskModal
        isOpen={showCreateTaskModal}
        onClose={() => setShowCreateTaskModal(false)}
        onTaskCreated={handleTaskCreated}
      />
    </div>
  );
};

export default Dashboard;

