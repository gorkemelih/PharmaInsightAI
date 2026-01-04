"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

interface QueryBuilderProps {
    onQueryChange: (query: string, isValid: boolean) => void;
    disabled?: boolean;
}

// Query templates
const TEMPLATES = [
    {
        id: "adverse_effects",
        label: "Adverse Effects",
        icon: "⚠️",
        condition: "",
        outcome: "adverse effects OR side effects OR safety",
        population: "",
    },
    {
        id: "efficacy",
        label: "Efficacy vs Placebo",
        icon: "📊",
        condition: "",
        outcome: "efficacy OR effectiveness",
        population: "",
    },
    {
        id: "guidelines",
        label: "Treatment Guidelines",
        icon: "📋",
        condition: "",
        outcome: "guidelines OR recommendations OR management",
        population: "",
    },
    {
        id: "mortality",
        label: "Mortality/Survival",
        icon: "📈",
        condition: "",
        outcome: "mortality OR survival OR overall survival",
        population: "",
    },
];

// Study type filters
const STUDY_TYPES = [
    { value: "", label: "All Study Types" },
    { value: "systematic review", label: "Systematic Review" },
    { value: "meta-analysis", label: "Meta-Analysis" },
    { value: "randomized controlled trial", label: "RCT" },
    { value: "clinical trial", label: "Clinical Trial" },
    { value: "guideline", label: "Guideline" },
];

// Broad/vague terms that need more context
const VAGUE_TERMS = [
    "cancer", "diabetes", "heart", "disease", "treatment", "drug", "medicine",
    "health", "patient", "study", "research", "therapy", "effect", "clinical",
];

export function QueryBuilder({ onQueryChange, disabled = false }: QueryBuilderProps) {
    const [condition, setCondition] = useState("");
    const [outcome, setOutcome] = useState("");
    const [population, setPopulation] = useState("");
    const [studyType, setStudyType] = useState("");
    const [humanOnly, setHumanOnly] = useState(true);

    const [validationError, setValidationError] = useState<string | null>(null);

    // Build and validate query
    useEffect(() => {
        const { query, isValid, error } = buildQuery();
        setValidationError(error);
        onQueryChange(query, isValid);
    }, [condition, outcome, population, studyType, humanOnly]);

    const buildQuery = (): { query: string; isValid: boolean; error: string | null } => {
        const conditionTrimmed = condition.trim();
        const outcomeTrimmed = outcome.trim();
        const populationTrimmed = population.trim();

        // Validation: Condition is required
        if (!conditionTrimmed) {
            return { query: "", isValid: false, error: "Condition/Intervention is required" };
        }

        // Validation: Check for vague terms alone
        const conditionLower = conditionTrimmed.toLowerCase();
        if (VAGUE_TERMS.includes(conditionLower) && !outcomeTrimmed && !populationTrimmed) {
            return {
                query: "",
                isValid: false,
                error: `"${conditionTrimmed}" is too broad. Add an Outcome or Population.`
            };
        }

        // Validation: Minimum length
        if (conditionTrimmed.length < 3) {
            return { query: "", isValid: false, error: "Condition must be at least 3 characters" };
        }

        // Build query parts
        const parts: string[] = [];

        // Main condition/intervention
        parts.push(`(${conditionTrimmed})`);

        // Outcome
        if (outcomeTrimmed) {
            parts.push(`(${outcomeTrimmed})`);
        }

        // Population
        if (populationTrimmed) {
            parts.push(`(${populationTrimmed})`);
        }

        // Study type filter
        if (studyType) {
            parts.push(`(${studyType}[pt])`);
        }

        // Human only filter
        if (humanOnly) {
            parts.push("(humans[mesh])");
        }

        const finalQuery = parts.join(" AND ");

        return { query: finalQuery, isValid: true, error: null };
    };

    const applyTemplate = (template: typeof TEMPLATES[0]) => {
        if (template.outcome) {
            setOutcome(template.outcome);
        }
        if (template.population) {
            setPopulation(template.population);
        }
    };

    const { query } = buildQuery();

    return (
        <div className="space-y-4">
            {/* Template Buttons */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Quick Templates</label>
                <div className="flex flex-wrap gap-2">
                    {TEMPLATES.map((template) => (
                        <button
                            key={template.id}
                            type="button"
                            onClick={() => applyTemplate(template)}
                            disabled={disabled}
                            className="px-3 py-1.5 text-xs rounded-full border border-input bg-background hover:bg-muted transition-colors disabled:opacity-50"
                        >
                            {template.icon} {template.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* PICO Fields */}
            <div className="grid gap-4">
                {/* Condition/Intervention - Required */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">
                        Condition / Intervention <span className="text-red-500">*</span>
                    </label>
                    <input
                        type="text"
                        value={condition}
                        onChange={(e) => setCondition(e.target.value)}
                        placeholder="e.g., Pyrotinib, Metformin, Breast cancer surgery"
                        disabled={disabled}
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <p className="text-xs text-muted-foreground">
                        The drug, treatment, or condition you want to research
                    </p>
                </div>

                {/* Outcome */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">
                        Outcome <span className="text-muted-foreground">(recommended)</span>
                    </label>
                    <input
                        type="text"
                        value={outcome}
                        onChange={(e) => setOutcome(e.target.value)}
                        placeholder="e.g., Survival, Side effects, Quality of life"
                        disabled={disabled}
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <p className="text-xs text-muted-foreground">
                        What result or effect are you looking for?
                    </p>
                </div>

                {/* Population */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">
                        Population <span className="text-muted-foreground">(optional)</span>
                    </label>
                    <input
                        type="text"
                        value={population}
                        onChange={(e) => setPopulation(e.target.value)}
                        placeholder="e.g., Elderly patients, HER2-positive, Children"
                        disabled={disabled}
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <p className="text-xs text-muted-foreground">
                        Specific patient group or demographics
                    </p>
                </div>
            </div>

            {/* Filters Row */}
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium">Study Type</label>
                    <select
                        value={studyType}
                        onChange={(e) => setStudyType(e.target.value)}
                        disabled={disabled}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:opacity-50"
                    >
                        {STUDY_TYPES.map((type) => (
                            <option key={type.value} value={type.value}>
                                {type.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium">Filters</label>
                    <div className="flex items-center gap-2 h-10">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={humanOnly}
                                onChange={(e) => setHumanOnly(e.target.checked)}
                                disabled={disabled}
                                className="h-4 w-4 rounded border-gray-300"
                            />
                            <span className="text-sm">Human studies only</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Validation Error */}
            {validationError && (
                <div className="p-3 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
                    <span>⚠️</span>
                    <span>{validationError}</span>
                </div>
            )}

            {/* Final Query Preview */}
            {query && (
                <div className="p-3 bg-muted/50 rounded-lg border">
                    <div className="text-xs font-medium text-muted-foreground mb-1">Final Query</div>
                    <code className="text-sm break-all">{query}</code>
                </div>
            )}
        </div>
    );
}
