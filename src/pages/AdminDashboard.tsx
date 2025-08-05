
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { Check, X, User, Phone, Mail, Building, FileText, Calendar, Eye, Truck, LogOut } from 'lucide-react';
import ApplicationDetails from '@/components/ApplicationDetails';

interface PendingOfficer {
  id: number;
  id_number: string;
  email: string;
  phone_number: string;
  full_name: string;
  station: string;
  created_at: string;
}

interface Application {
  id: number;
  application_number: string;
  full_names: string;
  status: string;
  application_type: string;
  created_at: string;
  updated_at: string;
  officer_name: string;
  generated_id_number?: string;
  source_type?: string;
}

const AdminDashboard = () => {
  const [pendingOfficers, setPendingOfficers] = useState<PendingOfficer[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [approvedApplications, setApprovedApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApplicationId, setSelectedApplicationId] = useState<number | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    fetchPendingOfficers();
    fetchApplications();
    fetchApprovedApplications();
  }, []);

  const fetchPendingOfficers = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/officers/pending');
      const data = await response.json();
      
      if (response.ok) {
        setPendingOfficers(data.officers);
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to fetch pending officers",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/applications');
      const data = await response.json();
      
      if (response.ok) {
        setApplications(data.applications);
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to fetch applications",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (officerId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/admin/officers/${officerId}/approve`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success",
          description: "Officer approved successfully",
        });
        // Remove approved officer from the list
        setPendingOfficers(prev => prev.filter(officer => officer.id !== officerId));
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to approve officer",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleReject = async (officerId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/admin/officers/${officerId}/reject`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success",
          description: "Officer rejected",
        });
        // Remove rejected officer from the list
        setPendingOfficers(prev => prev.filter(officer => officer.id !== officerId));
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to reject officer",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleViewDetails = (applicationId: number) => {
    setSelectedApplicationId(applicationId);
    setDetailsOpen(true);
  };

  const fetchApprovedApplications = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/admin/applications/approved');
      const data = await response.json();
      
      if (response.ok) {
        setApprovedApplications(data.applications);
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to fetch approved applications",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleDispatch = async (applicationId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/admin/applications/${applicationId}/dispatch`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Success",
          description: "ID dispatched successfully",
        });
        // Remove dispatched application from approved list
        setApprovedApplications(prev => prev.filter(app => app.id !== applicationId));
      } else {
        toast({
          title: "Error",
          description: data.error || "Failed to dispatch ID",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    }
  };

  const handleApplicationUpdate = () => {
    fetchApplications();
    fetchApprovedApplications();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'approved':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'rejected':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'dispatched':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleLogout = () => {
    // Clear any stored authentication data
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminData');
    sessionStorage.removeItem('adminToken');
    sessionStorage.removeItem('adminData');
    
    toast({
      title: "Logged out",
      description: "You have been logged out successfully",
    });
    
    navigate('/admin');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-primary mb-8">Admin Dashboard</h1>
          <div className="text-center">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-primary">Admin Dashboard</h1>
          <Button 
            variant="outline" 
            onClick={handleLogout}
            className="flex items-center gap-2"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
        
        <Tabs defaultValue="applications" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="applications" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              ID Applications
            </TabsTrigger>
            <TabsTrigger value="dispatch" className="flex items-center gap-2">
              <Truck className="h-4 w-4" />
              Dispatch IDs
            </TabsTrigger>
            <TabsTrigger value="officers" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Officer Applications
            </TabsTrigger>
          </TabsList>

          <TabsContent value="applications">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  ID Applications Management
                </CardTitle>
                <CardDescription>
                  Review and manage citizen ID applications
                </CardDescription>
              </CardHeader>
              <CardContent>
                {applications.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No ID applications found
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Application Details</TableHead>
                          <TableHead>Applicant Name</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Processing Officer</TableHead>
                          <TableHead>Application Date</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {applications.map((application) => (
                          <TableRow key={`${application.source_type || 'regular'}-${application.id}`}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{application.application_number}</div>
                                <div className="text-sm text-muted-foreground">
                                  ID: {application.id} {application.source_type === 'lost_id' ? '(Renewal)' : ''}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="font-medium">{application.full_names}</div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="capitalize">
                                {application.application_type}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">{application.officer_name}</div>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {formatDate(application.created_at)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge className={getStatusColor(application.status)}>
                                {application.status.toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleViewDetails(application.id)}
                              >
                                <Eye className="h-4 w-4 mr-1" />
                                View Details
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dispatch">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Dispatch Approved IDs
                </CardTitle>
                <CardDescription>
                  Dispatch approved ID cards to applicants
                </CardDescription>
              </CardHeader>
              <CardContent>
                {approvedApplications.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No approved applications ready for dispatch
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Application Details</TableHead>
                          <TableHead>Applicant Name</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Generated ID Number</TableHead>
                          <TableHead>Approved Date</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {approvedApplications.map((application) => (
                          <TableRow key={application.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{application.application_number}</div>
                                <div className="text-sm text-muted-foreground">
                                  ID: {application.id}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="font-medium">{application.full_names}</div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="capitalize">
                                {application.application_type}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="font-mono text-sm bg-muted px-2 py-1 rounded">
                                {application.generated_id_number || 'N/A'}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {formatDate(application.updated_at)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                onClick={() => handleDispatch(application.id)}
                                className="bg-purple-600 hover:bg-purple-700"
                              >
                                <Truck className="h-4 w-4 mr-1" />
                                Dispatch
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="officers">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Officer Applications - Pending Approval
                </CardTitle>
                <CardDescription>
                  Review and approve officer applications to grant system access
                </CardDescription>
              </CardHeader>
              <CardContent>
                {pendingOfficers.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No pending officer applications
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Officer Details</TableHead>
                          <TableHead>Contact Information</TableHead>
                          <TableHead>Station</TableHead>
                          <TableHead>Applied Date</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pendingOfficers.map((officer) => (
                          <TableRow key={officer.id}>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="font-medium">{officer.full_name}</div>
                                <div className="text-sm text-muted-foreground">
                                  ID: {officer.id_number}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm">
                                  <Mail className="h-4 w-4" />
                                  {officer.email}
                                </div>
                                <div className="flex items-center gap-2 text-sm">
                                  <Phone className="h-4 w-4" />
                                  {officer.phone_number}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Building className="h-4 w-4" />
                                {officer.station}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {formatDate(officer.created_at)}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="secondary">Pending</Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="default"
                                  onClick={() => handleApprove(officer.id)}
                                  className="bg-green-600 hover:bg-green-700"
                                >
                                  <Check className="h-4 w-4 mr-1" />
                                  Approve
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => handleReject(officer.id)}
                                >
                                  <X className="h-4 w-4 mr-1" />
                                  Reject
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {selectedApplicationId && (
          <ApplicationDetails
            applicationId={selectedApplicationId}
            open={detailsOpen}
            onClose={() => setDetailsOpen(false)}
            onUpdate={handleApplicationUpdate}
          />
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
