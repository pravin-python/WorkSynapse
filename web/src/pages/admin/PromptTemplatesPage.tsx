import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus, Save, Trash2, Edit } from 'lucide-react';

// Mock data (replace with API call)
const initialTemplates = [
    {
        id: 1,
        name: "Standard Assistant",
        system_prompt: "You are a helpful assistant.",
        goal_prompt: "Assist the user with their tasks.",
        instruction_prompt: "Be concise and clear.",
        tool_prompt: "",
        output_prompt: "Markdown format.",
        is_active: true
    }
];

export default function PromptTemplatesPage() {
    const [templates, setTemplates] = useState(initialTemplates);
    const [isEditing, setIsEditing] = useState(false);
    const [currentTemplate, setCurrentTemplate] = useState<any>(null);

    const handleEdit = (template: any) => {
        setCurrentTemplate({ ...template });
        setIsEditing(true);
    };

    const handleCreate = () => {
        setCurrentTemplate({
            id: Date.now(),
            name: "New Template",
            system_prompt: "",
            goal_prompt: "",
            instruction_prompt: "",
            tool_prompt: "",
            output_prompt: "",
            is_active: true
        });
        setIsEditing(true);
    };

    const handleSave = () => {
        // API call would go here
        if (templates.find(t => t.id === currentTemplate.id)) {
            setTemplates(templates.map(t => t.id === currentTemplate.id ? currentTemplate : t));
        } else {
            setTemplates([...templates, currentTemplate]);
        }
        setIsEditing(false);
    };

    const handleDelete = (id: number) => {
        setTemplates(templates.filter(t => t.id !== id));
    };

    if (isEditing) {
        return (
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <h2 className="text-3xl font-bold tracking-tight">
                        {currentTemplate.id ? 'Edit Template' : 'Create Template'}
                    </h2>
                    <div className="space-x-2">
                        <Button variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
                        <Button onClick={handleSave}><Save className="mr-2 h-4 w-4" /> Save Template</Button>
                    </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                    <Card className="col-span-2">
                        <CardHeader>
                            <CardTitle>Basic Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Template Name</Label>
                                <Input
                                    value={currentTemplate.name}
                                    onChange={(e) => setCurrentTemplate({ ...currentTemplate, name: e.target.value })}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="col-span-2 md:col-span-1">
                        <CardHeader>
                            <CardTitle>System & Identity</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>System Prompt (Identity)</Label>
                                <Textarea
                                    className="min-h-[150px] font-mono text-sm"
                                    value={currentTemplate.system_prompt}
                                    onChange={(e) => setCurrentTemplate({ ...currentTemplate, system_prompt: e.target.value })}
                                    placeholder="You are a senior engineer..."
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Goal Prompt</Label>
                                <Textarea
                                    className="min-h-[100px] font-mono text-sm"
                                    value={currentTemplate.goal_prompt}
                                    onChange={(e) => setCurrentTemplate({ ...currentTemplate, goal_prompt: e.target.value })}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="col-span-2 md:col-span-1">
                        <CardHeader>
                            <CardTitle>Execution Rules</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Instruction Prompt</Label>
                                <Textarea
                                    className="min-h-[150px] font-mono text-sm"
                                    value={currentTemplate.instruction_prompt}
                                    onChange={(e) => setCurrentTemplate({ ...currentTemplate, instruction_prompt: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Output Format</Label>
                                <Textarea
                                    className="min-h-[100px] font-mono text-sm"
                                    value={currentTemplate.output_prompt}
                                    onChange={(e) => setCurrentTemplate({ ...currentTemplate, output_prompt: e.target.value })}
                                    placeholder="Return JSON..."
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="col-span-2">
                        <CardHeader>
                            <CardTitle>Tools Configuration (Optional)</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Tool Prompt (Override auto-generation)</Label>
                                <Textarea
                                    className="min-h-[100px] font-mono text-sm"
                                    value={currentTemplate.tool_prompt}
                                    onChange={(e) => setCurrentTemplate({ ...currentTemplate, tool_prompt: e.target.value })}
                                />
                                <p className="text-sm text-gray-500">
                                    Leave empty to let the Orchestrator auto-generate tool descriptions based on available tools.
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Prompt Templates</h2>
                    <p className="text-muted-foreground">Manage structured prompts for your agents.</p>
                </div>
                <Button onClick={handleCreate}>
                    <Plus className="mr-2 h-4 w-4" /> Create Template
                </Button>
            </div>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Name</TableHead>
                                <TableHead>System Prompt Preview</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {templates.map((template) => (
                                <TableRow key={template.id}>
                                    <TableCell className="font-medium">{template.name}</TableCell>
                                    <TableCell className="truncate max-w-[300px] text-muted-foreground">
                                        {template.system_prompt}
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={template.is_active ? "default" : "secondary"}>
                                            {template.is_active ? "Active" : "Inactive"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="ghost" size="icon" onClick={() => handleEdit(template)}>
                                            <Edit className="h-4 w-4" />
                                        </Button>
                                        <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleDelete(template.id)}>
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
