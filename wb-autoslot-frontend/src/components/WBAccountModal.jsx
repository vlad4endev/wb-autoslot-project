import React, { useState } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Textarea } from '@/components/ui/textarea.jsx';
import { X, Settings, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const WBAccountModal = ({ isOpen, onClose, onSuccess }) => {
  const [accountName, setAccountName] = useState('');
  const [cookies, setCookies] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const { apiCall } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (!accountName.trim()) {
      setError('Введите название аккаунта');
      setLoading(false);
      return;
    }

    try {
      const response = await apiCall('/wb-accounts', {
        method: 'POST',
        body: JSON.stringify({
          account_name: accountName.trim(),
          cookies: cookies.trim()
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Аккаунт WB успешно добавлен!');
        setTimeout(() => {
          onSuccess && onSuccess(data.account);
          handleClose();
        }, 1500);
      } else {
        setError(data.error || 'Ошибка при добавлении аккаунта');
      }
    } catch (error) {
      setError('Произошла ошибка. Попробуйте еще раз.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setAccountName('');
    setCookies('');
    setError('');
    setSuccess('');
    setLoading(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Подключить аккаунт Wildberries
            </CardTitle>
            <CardDescription>
              Добавьте свой аккаунт WB для автоматического поиска и бронирования слотов
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            {success && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="accountName">Название аккаунта</Label>
              <Input
                id="accountName"
                placeholder="Например: Основной аккаунт"
                value={accountName}
                onChange={(e) => setAccountName(e.target.value)}
                required
              />
              <p className="text-sm text-gray-500">
                Придумайте название для удобного управления аккаунтами
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="cookies">Cookies (необязательно)</Label>
              <Textarea
                id="cookies"
                placeholder="Вставьте cookies из браузера для автоматической авторизации"
                value={cookies}
                onChange={(e) => setCookies(e.target.value)}
                rows={4}
                className="resize-none"
              />
              <div className="text-sm text-gray-500 space-y-1">
                <p>• Откройте личный кабинет WB в браузере</p>
                <p>• Нажмите F12 → Application → Cookies</p>
                <p>• Скопируйте все cookies и вставьте сюда</p>
                <p>• Или оставьте пустым для ручной авторизации</p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                className="flex-1"
                disabled={loading}
              >
                Отмена
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={loading}
              >
                {loading ? 'Добавление...' : 'Добавить аккаунт'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default WBAccountModal;

