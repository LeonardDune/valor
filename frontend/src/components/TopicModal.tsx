import React, { useState } from 'react';
import { Target } from 'lucide-react';

interface TopicModalProps {
    onSubmit: (topic: string) => void;
}

const TopicModal: React.FC<TopicModalProps> = ({ onSubmit }) => {
    const [topic, setTopic] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (topic.trim()) {
            onSubmit(topic.trim());
        }
    };

    return (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="bg-indigo-600 p-6 text-white text-center">
                    <div className="mx-auto w-12 h-12 bg-indigo-500 rounded-xl flex items-center justify-center mb-4">
                        <Target className="w-6 h-6 text-white" />
                    </div>
                    <h2 className="text-xl font-bold">Nieuwe Sessie Starten</h2>
                    <p className="text-indigo-100 mt-2 text-sm">Definieer het centrale probleem of thema voor deze analyse.</p>
                </div>

                <form onSubmit={handleSubmit} className="p-6">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Centraal Thema / Probleem</label>
                            <textarea
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                placeholder="bijv. Te veel stikstof in het milieu"
                                className="w-full p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none min-h-[100px] resize-none"
                                autoFocus
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={!topic.trim()}
                            className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Start Analyse
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TopicModal;
