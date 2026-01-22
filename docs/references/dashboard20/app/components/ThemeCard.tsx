import { MoreVertical, Activity, Users, MessageSquare } from 'lucide-react';

export interface Theme {
  id: string;
  name: string;
  description: string;
  organization: string;
  project?: string;
  perspectives: {
    name: string;
    color: string;
    progress: number;
  }[];
  activity: {
    comments: number;
    members: number;
    lastUpdate: string;
  };
}

interface ThemeCardProps {
  theme: Theme;
}

export function ThemeCard({ theme }: ThemeCardProps) {
  return (
    <div className="bg-white rounded-xl border border-border p-6 hover:shadow-lg transition-shadow duration-300 group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="font-semibold text-foreground mb-1">{theme.name}</h3>
          <p className="text-sm text-muted-foreground line-clamp-2">{theme.description}</p>
        </div>
        <button className="w-8 h-8 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-accent transition-all">
          <MoreVertical className="w-4 h-4 text-muted-foreground" />
        </button>
      </div>

      {/* Context Badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="px-3 py-1 bg-accent/50 text-accent-foreground rounded-full text-xs">
          {theme.organization}
        </span>
        {theme.project && (
          <span className="px-3 py-1 bg-muted/50 text-muted-foreground rounded-full text-xs">
            {theme.project}
          </span>
        )}
      </div>

      {/* Perspectives */}
      <div className="space-y-3 mb-4">
        <div className="text-xs text-muted-foreground uppercase tracking-wider">Perspectieven</div>
        <div className="grid grid-cols-2 gap-2">
          {theme.perspectives.map((perspective) => (
            <button
              key={perspective.name}
              className="p-3 rounded-lg border border-border hover:border-current hover:shadow-sm transition-all text-left group/perspective"
              style={{ borderColor: `${perspective.color}20` }}
            >
              <div className="flex items-center justify-between mb-2">
                <span 
                  className="text-xs font-medium"
                  style={{ color: perspective.color }}
                >
                  {perspective.name}
                </span>
                <span className="text-xs text-muted-foreground">{perspective.progress}%</span>
              </div>
              <div className="h-1 bg-accent rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all"
                  style={{ 
                    width: `${perspective.progress}%`,
                    backgroundColor: perspective.color 
                  }}
                />
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Activity Footer */}
      <div className="flex items-center gap-4 pt-4 border-t border-border text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <MessageSquare className="w-4 h-4" />
          <span>{theme.activity.comments}</span>
        </div>
        <div className="flex items-center gap-1">
          <Users className="w-4 h-4" />
          <span>{theme.activity.members}</span>
        </div>
        <div className="flex items-center gap-1 ml-auto">
          <Activity className="w-4 h-4" />
          <span>{theme.activity.lastUpdate}</span>
        </div>
      </div>
    </div>
  );
}
