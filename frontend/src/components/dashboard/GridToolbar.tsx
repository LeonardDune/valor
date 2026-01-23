import React from 'react';
import { Search, Filter, SortAsc, LayoutGrid } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuCheckboxItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export interface FilterOption {
    label: string;
    field: string;
    options: { label: string; value: string }[];
}

export interface SortOption {
    label: string;
    value: string;
}

export interface GroupOption {
    label: string;
    value: string;
}

interface GridToolbarProps {
    searchPlaceholder?: string;
    onSearch: (query: string) => void;
    // Sorting
    sortOptions: SortOption[];
    currentSort: string;
    onSortChange: (value: string) => void;
    // Grouping
    groupOptions?: GroupOption[];
    currentGroup?: string;
    onGroupChange?: (value: string) => void;
    // Filtering
    filterConfig?: FilterOption[];
    activeFilters?: Record<string, string[]>;
    onFilterChange?: (field: string, values: string[]) => void;
    // Actions
    extraActions?: React.ReactNode;
}

export const GridToolbar: React.FC<GridToolbarProps> = ({
    searchPlaceholder = "Zoeken...",
    onSearch,
    sortOptions,
    currentSort,
    onSortChange,
    groupOptions,
    currentGroup,
    onGroupChange,
    filterConfig,
    activeFilters = {},
    onFilterChange,
    extraActions
}) => {
    return (
        <div className="flex flex-col gap-4 md:flex-row md:items-center justify-between bg-card/50 p-4 rounded-xl border border-border/50 backdrop-blur-sm mb-6">
            <div className="flex flex-1 items-center gap-2 max-w-sm">
                <div className="relative w-full">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder={searchPlaceholder}
                        className="pl-9 bg-background/50 border-border/50 focus-visible:ring-primary/20"
                        onChange={(e) => onSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
                {/* Filters */}
                {filterConfig && filterConfig.length > 0 && onFilterChange && (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm" className="h-9 gap-2 border-border/50 bg-background/50">
                                <Filter className="h-4 w-4" />
                                <span>Filters</span>
                                {Object.values(activeFilters).flat().length > 0 && (
                                    <span className="ml-1 px-1.5 py-0.5 rounded-full bg-primary text-[10px] font-bold text-primary-foreground min-w-[1.2rem]">
                                        {Object.values(activeFilters).flat().length}
                                    </span>
                                )}
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            <DropdownMenuLabel>Filter op</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            {filterConfig.map((config) => (
                                <React.Fragment key={config.field}>
                                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                        {config.label}
                                    </div>
                                    {config.options.map((opt) => (
                                        <DropdownMenuCheckboxItem
                                            key={opt.value}
                                            checked={activeFilters[config.field]?.includes(opt.value)}
                                            onCheckedChange={(checked) => {
                                                const current = activeFilters[config.field] || [];
                                                const next = checked
                                                    ? [...current, opt.value]
                                                    : current.filter(v => v !== opt.value);
                                                onFilterChange(config.field, next);
                                            }}
                                        >
                                            {opt.label}
                                        </DropdownMenuCheckboxItem>
                                    ))}
                                    <DropdownMenuSeparator />
                                </React.Fragment>
                            ))}
                            <Button
                                variant="ghost"
                                size="sm"
                                className="w-full justify-start text-xs text-muted-foreground hover:text-foreground"
                                onClick={() => {
                                    filterConfig.forEach(c => onFilterChange(c.field, []));
                                }}
                            >
                                Filters wissen
                            </Button>
                        </DropdownMenuContent>
                    </DropdownMenu>
                )}

                {/* Sorteren */}
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground hidden sm:inline">Sorteren:</span>
                    <Select value={currentSort} onValueChange={onSortChange}>
                        <SelectTrigger className="h-9 w-[160px] bg-background/50 border-border/50">
                            <div className="flex items-center gap-2 shrink-0">
                                <SortAsc className="h-3.5 w-3.5 text-muted-foreground" />
                                <SelectValue placeholder="Sorteer op" />
                            </div>
                        </SelectTrigger>
                        <SelectContent>
                            {sortOptions.map((opt) => (
                                <SelectItem key={opt.value} value={opt.value}>
                                    {opt.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {/* Groeperen */}
                {groupOptions && groupOptions.length > 0 && onGroupChange && (
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground hidden sm:inline">Groeperen:</span>
                        <Select value={currentGroup || 'none'} onValueChange={onGroupChange}>
                            <SelectTrigger className="h-9 w-[160px] bg-background/50 border-border/50">
                                <div className="flex items-center gap-2 shrink-0">
                                    <LayoutGrid className="h-3.5 w-3.5 text-muted-foreground" />
                                    <SelectValue placeholder="Groepeer op" />
                                </div>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">Geen groepering</SelectItem>
                                {groupOptions.map((opt) => (
                                    <SelectItem key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                )}

                {extraActions && (
                    <>
                        <div className="w-px h-6 bg-border/50 mx-1 hidden sm:block" />
                        {extraActions}
                    </>
                )}
            </div>
        </div>
    );
};
