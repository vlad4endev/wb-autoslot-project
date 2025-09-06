import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Checkbox } from '@/components/ui/checkbox.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { X, Calendar, Package, Truck, Settings } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const CreateTaskModal = ({ isOpen, onClose, onTaskCreated }) => {
  const { apiCall } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [wbAccounts, setWbAccounts] = useState([]);
  
  const [formData, setFormData] = useState({
    name: '',
    warehouse: '',
    date_from: '',
    date_to: '',
    coefficient: '',
    packaging: 'boxes',
    wb_account_id: '',
    auto_book: false
  });

  const warehouses = [
    'Коледино',
    'Подольск',
    'Электросталь',
    'Казань',
    'Екатеринбург',
    'Новосибирск',
    'Хабаровск',
    'Краснодар',
    'Санкт-Петербург',
    'Тула',
    'Белые Столбы',
    'Домодедово',
    'Чехов',
    'Невинномысск'
  ];

  useEffect(() => {
    if (isOpen) {
      fetchWBAccounts();
      resetForm();
    }
  }, [isOpen]);

  const fetchWBAccounts = async () => {
    try {
      const response = await apiCall('/wb-accounts');
      if (response.ok) {
        const data = await response.json();
        setWbAccounts(data.accounts || []);
      }
    } catch (error) {
      console.error('Error fetching WB accounts:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      warehouse: '',
      date_from: '',
      date_to: '',
      coefficient: '',
      packaging: 'boxes',
      wb_account_id: '',
      auto_book: false
    });
    setError('');
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Введите название задачи');
      return false;
    }
    if (!formData.warehouse) {
      setError('Выберите склад');
      return false;
    }
    if (!formData.date_from || !formData.date_to) {
      setError('Укажите период поиска');
      return false;
    }
    if (new Date(formData.date_from) >= new Date(formData.date_to)) {
      setError('Дата окончания должна быть позже даты начала');
      return false;
    }
    if (!formData.coefficient || parseFloat(formData.coefficient) <= 0) {
      setError('Укажите корректный минимальный коэффициент');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setError('');

    try {
      // Ensure dates are in YYYY-MM-DD format
      const taskData = {
        ...formData,
        date_from: formData.date_from ? new Date(formData.date_from).toISOString().split('T')[0] : '',
        date_to: formData.date_to ? new Date(formData.date_to).toISOString().split('T')[0] : ''
      };

      const response = await apiCall('/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
      });

      if (response.ok) {
        const data = await response.json();
        onTaskCreated(data.task);
        onClose();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка создания задачи');
      }
    } catch (error) {
      setError('Ошибка сети');
      console.error('Create task error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Создать задачу поиска слотов
              </CardTitle>
              <CardDescription>
                Настройте параметры поиска доступных слотов на Wildberries
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Task Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Название задачи</Label>
              <Input
                id="name"
                placeholder="Например: Поиск слотов на Коледино"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
            </div>

            {/* Period */}
            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Период поиска
              </Label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="date_from" className="text-sm text-gray-600">Дата начала</Label>
                  <Input
                    id="date_from"
                    type="date"
                    value={formData.date_from}
                    onChange={(e) => handleInputChange('date_from', e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="date_to" className="text-sm text-gray-600">Дата окончания</Label>
                  <Input
                    id="date_to"
                    type="date"
                    value={formData.date_to}
                    onChange={(e) => handleInputChange('date_to', e.target.value)}
                    min={formData.date_from || new Date().toISOString().split('T')[0]}
                    required
                  />
                </div>
              </div>
            </div>

            {/* Warehouse */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Truck className="h-4 w-4" />
                Склад
              </Label>
              <Select value={formData.warehouse} onValueChange={(value) => handleInputChange('warehouse', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите склад" />
                </SelectTrigger>
                <SelectContent>
                  {warehouses.map((warehouse) => (
                    <SelectItem key={warehouse} value={warehouse}>
                      {warehouse}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Coefficient */}
            <div className="space-y-2">
              <Label htmlFor="coefficient">Минимальный коэффициент</Label>
              <Input
                id="coefficient"
                type="number"
                step="0.1"
                min="0.1"
                placeholder="Например: 1.5"
                value={formData.coefficient}
                onChange={(e) => handleInputChange('coefficient', e.target.value)}
                required
              />
              <p className="text-sm text-gray-500">
                Задачи будут искать слоты с коэффициентом не ниже указанного
              </p>
            </div>

            {/* Packaging Type */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Package className="h-4 w-4" />
                Тип упаковки
              </Label>
              <Select value={formData.packaging} onValueChange={(value) => handleInputChange('packaging', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="boxes">Короба</SelectItem>
                  <SelectItem value="pallets">Палеты</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* WB Account */}
            {wbAccounts.length > 0 && (
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Аккаунт WB (опционально)
                </Label>
                <Select value={formData.wb_account_id} onValueChange={(value) => handleInputChange('wb_account_id', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Выберите аккаунт WB" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Без привязки к аккаунту</SelectItem>
                    {wbAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id.toString()}>
                        {account.account_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Auto Booking */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="auto_book"
                checked={formData.auto_book}
                onCheckedChange={(checked) => handleInputChange('auto_book', checked)}
              />
              <Label htmlFor="auto_book" className="text-sm">
                Автоматически бронировать найденные слоты
              </Label>
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Отмена
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Создание...' : 'Поиск слотов'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CreateTaskModal;

