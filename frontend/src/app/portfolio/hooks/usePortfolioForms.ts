import { useState } from 'react';
import { Position, AddPositionPayload, UpdatePositionPayload } from '@/types';

interface UsePortfolioFormsProps {
    submitAddPosition: (data: any, options: any) => Promise<void>;
    submitUpdatePosition: (position: Position | null, data: any, options: any) => Promise<void>;
}

export function usePortfolioForms({ submitAddPosition, submitUpdatePosition }: UsePortfolioFormsProps) {
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
    const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

    const [formData, setFormData] = useState({
        ticker: '',
        shares: '',
        price: '',
        sl: '',
        tp: '',
        tp2: '',
        date: ''
    });

    const handleFormFieldChange = (field: keyof typeof formData, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleAddPosition = async (e: React.FormEvent) => {
        e.preventDefault();
        await submitAddPosition(formData, {
            closeModal: () => setIsAddModalOpen(false),
            resetForm: () => setFormData({ ticker: '', shares: '', price: '', sl: '', tp: '', tp2: '', date: '' }),
        });
    };

    const handleUpdatePosition = async (e: React.FormEvent) => {
        e.preventDefault();
        await submitUpdatePosition(selectedPosition, formData, {
            onComplete: () => {
                setIsUpdateModalOpen(false);
                setSelectedPosition(null);
            },
        });
    };

    return {
        isAddModalOpen,
        setIsAddModalOpen,
        isUpdateModalOpen,
        setIsUpdateModalOpen,
        selectedPosition,
        setSelectedPosition,
        formData,
        setFormData,
        handleFormFieldChange,
        handleAddPosition,
        handleUpdatePosition,
    };
}
