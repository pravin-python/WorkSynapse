import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import { Upload, FileText, Database, RefreshCw, Search } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';

// Mock data
const mockSources = [
    { id: 1, name: "Project_Specs_v1.pdf", type: "file", status: "Active", chunks: 45, date: "2023-10-27" },
    { id: 2, name: "Meeting Notes - Q4 Planning", type: "note", status: "Active", chunks: 12, date: "2023-10-26" },
    { id: 3, name: "API Documentation", type: "url", status: "Processing", chunks: 0, date: "2023-10-28" },
];

const mockChunks = [
    { id: 1, source: "Project_Specs_v1.pdf", content: "The system shall support real-time collaboration...", score: 0.89 },
    { id: 2, source: "Project_Specs_v1.pdf", content: "Architecture diagram references module X...", score: 0.85 },
    { id: 3, source: "Meeting Notes", content: "We decided to go with PGVector for production...", score: 0.82 },
];

export default function KnowledgeBasePage() {
    const [sources, setSources] = useState(mockSources);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState(mockChunks);

    const handleUpload = () => {
        // Placeholder for upload logic
        alert("Upload functionality to be integrated with API.");
    };

    const handleSearch = () => {
        // Placeholder for search logic
        console.log("Searching for:", searchQuery);
    };

    return (
        <div className="space-y-6">
            <PageHeader
                title="RAG Knowledge Base"
                subtitle="Manage knowledge sources and view indexed chunks."
                action={
                    <div className="flex space-x-2">
                        <Button variant="outline">
                            <RefreshCw className="mr-2 h-4 w-4" /> Re-index
                        </Button>
                        <Button onClick={handleUpload}>
                            <Upload className="mr-2 h-4 w-4" /> Upload Document
                        </Button>
                    </div>
                }
            />

            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
                        <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{sources.length}</div>
                        <p className="text-xs text-muted-foreground">+2 from last week</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Indexed Chunks</CardTitle>
                        <Database className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">1,245</div>
                        <p className="text-xs text-muted-foreground">Across all sources</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Vector Store</CardTitle>
                        <Badge variant="outline">PGVector</Badge>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">Active</div>
                        <p className="text-xs text-muted-foreground">Production Mode</p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="sources" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="sources">Knowledge Sources</TabsTrigger>
                    <TabsTrigger value="explorer">Chunk Explorer</TabsTrigger>
                </TabsList>

                <TabsContent value="sources" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Sources</CardTitle>
                            <CardDescription>
                                Files, notes, and external links currently indexed.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Chunks</TableHead>
                                        <TableHead>Date Added</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {sources.map((source) => (
                                        <TableRow key={source.id}>
                                            <TableCell className="font-medium">{source.name}</TableCell>
                                            <TableCell>
                                                <Badge variant="secondary">{source.type}</Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant={source.status === "Active" ? "outline" : "secondary"}>
                                                    {source.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>{source.chunks}</TableCell>
                                            <TableCell>{source.date}</TableCell>
                                            <TableCell className="text-right">
                                                <Button variant="ghost" size="sm" className="text-red-500">Remove</Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="explorer" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Semantic Search</CardTitle>
                            <CardDescription>
                                Test retrieval and inspect chunks.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex gap-2">
                                <Input
                                    placeholder="Ask a question to test retrieval..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                                <Button onClick={handleSearch}>
                                    <Search className="mr-2 h-4 w-4" /> Search
                                </Button>
                            </div>

                            <div className="space-y-4 pt-4">
                                {searchResults.map((chunk) => (
                                    <div key={chunk.id} className="p-4 border rounded-lg bg-muted/50">
                                        <div className="flex justify-between mb-2">
                                            <Badge variant="outline">{chunk.source}</Badge>
                                            <span className="text-sm text-gray-500">Score: {chunk.score}</span>
                                        </div>
                                        <p className="text-sm font-mono text-gray-700 dark:text-gray-300">
                                            {chunk.content}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
