import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Search, Upload, CreditCard, Smartphone, ArrowLeft } from 'lucide-react';

interface CitizenDetails {
  id_number: string;
  full_names: string;
  date_of_birth: string;
  place_of_birth: string;
  gender: string;
  nationality: string;
}

const LostIdReplacement = () => {
  const [step, setStep] = useState(1);
  const [idNumber, setIdNumber] = useState('');
  const [citizenDetails, setCitizenDetails] = useState<CitizenDetails | null>(null);
  const [obNumber, setObNumber] = useState('');
  const [obDescription, setObDescription] = useState('');
  const [obPhoto, setObPhoto] = useState<File | null>(null);
  const [passportPhoto, setPassportPhoto] = useState<File | null>(null);
  const [birthCertPhoto, setBirthCertPhoto] = useState<File | null>(null);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [loading, setLoading] = useState(false);
  const [waitingCardNumber, setWaitingCardNumber] = useState('');
  
  const navigate = useNavigate();
  const { toast } = useToast();

  const searchIdDetails = async () => {
    if (!idNumber.trim()) {
      toast({
        title: "Error",
        description: "Please enter an ID number",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/citizen/${idNumber}`);
      if (response.ok) {
        const data = await response.json();
        setCitizenDetails(data);
        setStep(2);
      } else {
        toast({
          title: "ID Not Found",
          description: "No citizen found with this ID number",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to search ID details",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (file: File, type: 'ob' | 'passport' | 'birth') => {
    if (type === 'ob') setObPhoto(file);
    else if (type === 'passport') setPassportPhoto(file);
    else if (type === 'birth') setBirthCertPhoto(file);
  };

  const proceedToPayment = () => {
    if (!obNumber.trim() || !obDescription.trim() || !obPhoto || !passportPhoto || !birthCertPhoto) {
      toast({
        title: "Missing Information",
        description: "Please fill all fields and upload all required documents",
        variant: "destructive"
      });
      return;
    }
    setStep(3);
  };

  const submitApplication = async () => {
    if (!paymentMethod) {
      toast({
        title: "Payment Method Required",
        description: "Please select a payment method",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('id_number', idNumber);
      formData.append('ob_number', obNumber);
      formData.append('ob_description', obDescription);
      formData.append('payment_method', paymentMethod);
      formData.append('ob_photo', obPhoto!);
      formData.append('passport_photo', passportPhoto!);
      formData.append('birth_certificate', birthCertPhoto!);

      const officerData = localStorage.getItem('officerData');
      if (officerData) {
        const officer = JSON.parse(officerData);
        formData.append('officer_id', officer.id);
      }

      const response = await fetch('http://localhost:5000/api/lost-id-applications', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setWaitingCardNumber(data.waiting_card_number);
        setStep(4);
        toast({
          title: "Application Submitted",
          description: "Lost ID replacement application submitted successfully",
        });
      } else {
        throw new Error('Failed to submit application');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to submit application",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <Button 
            variant="outline" 
            onClick={() => navigate('/officer/dashboard')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Button>
          <h1 className="text-3xl font-bold text-primary">Lost ID Replacement</h1>
        </div>

        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Search Citizen Details
              </CardTitle>
              <CardDescription>
                Enter the ID number of the lost ID to retrieve citizen details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="idNumber">ID Number</Label>
                <Input
                  id="idNumber"
                  value={idNumber}
                  onChange={(e) => setIdNumber(e.target.value)}
                  placeholder="Enter ID number"
                />
              </div>
              <Button 
                onClick={searchIdDetails} 
                disabled={loading}
                className="w-full"
              >
                {loading ? 'Searching...' : 'Search ID Details'}
              </Button>
            </CardContent>
          </Card>
        )}

        {step === 2 && citizenDetails && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Citizen Details</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Full Names</Label>
                  <p className="font-medium">{citizenDetails.full_names}</p>
                </div>
                <div>
                  <Label>ID Number</Label>
                  <p className="font-medium">{citizenDetails.id_number}</p>
                </div>
                <div>
                  <Label>Date of Birth</Label>
                  <p className="font-medium">{citizenDetails.date_of_birth}</p>
                </div>
                <div>
                  <Label>Gender</Label>
                  <p className="font-medium">{citizenDetails.gender}</p>
                </div>
                <div>
                  <Label>Place of Birth</Label>
                  <p className="font-medium">{citizenDetails.place_of_birth}</p>
                </div>
                <div>
                  <Label>Nationality</Label>
                  <p className="font-medium">{citizenDetails.nationality}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Lost ID Documentation
                </CardTitle>
                <CardDescription>
                  Provide OB details and upload required documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="obNumber">OB Number</Label>
                  <Input
                    id="obNumber"
                    value={obNumber}
                    onChange={(e) => setObNumber(e.target.value)}
                    placeholder="Enter OB number"
                  />
                </div>
                
                <div>
                  <Label htmlFor="obDescription">OB Description</Label>
                  <Textarea
                    id="obDescription"
                    value={obDescription}
                    onChange={(e) => setObDescription(e.target.value)}
                    placeholder="Describe how the ID was lost"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>OB Photo</Label>
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'ob')}
                    />
                    {obPhoto && <p className="text-sm text-muted-foreground mt-1">✓ {obPhoto.name}</p>}
                  </div>
                  
                  <div>
                    <Label>New Passport Photo</Label>
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'passport')}
                    />
                    {passportPhoto && <p className="text-sm text-muted-foreground mt-1">✓ {passportPhoto.name}</p>}
                  </div>
                  
                  <div>
                    <Label>Birth Certificate Photo</Label>
                    <Input
                      type="file"
                      accept="image/*"
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'birth')}
                    />
                    {birthCertPhoto && <p className="text-sm text-muted-foreground mt-1">✓ {birthCertPhoto.name}</p>}
                  </div>
                </div>

                <Button onClick={proceedToPayment} className="w-full">
                  Proceed to Payment
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Payment Method</CardTitle>
              <CardDescription>
                Select payment method for ID replacement fee (KES 1,000)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                  onClick={() => setPaymentMethod('cash')}
                  className="h-20 flex flex-col items-center gap-2"
                >
                  <CreditCard className="h-6 w-6" />
                  Cash Payment
                </Button>
                
                <Button
                  variant={paymentMethod === 'mpesa' ? 'default' : 'outline'}
                  onClick={() => setPaymentMethod('mpesa')}
                  className="h-20 flex flex-col items-center gap-2"
                >
                  <Smartphone className="h-6 w-6" />
                  M-Pesa
                </Button>
              </div>

              {paymentMethod && (
                <div className="mt-6">
                  <div className="bg-muted p-4 rounded-lg mb-4">
                    <h3 className="font-semibold mb-2">Payment Summary</h3>
                    <div className="flex justify-between">
                      <span>ID Replacement Fee</span>
                      <span className="font-medium">KES 1,000</span>
                    </div>
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>Payment Method</span>
                      <span>{paymentMethod === 'cash' ? 'Cash' : 'M-Pesa'}</span>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={submitApplication} 
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? 'Submitting...' : 'Submit Application for Approval'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {step === 4 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-green-600">Application Submitted Successfully!</CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="font-semibold text-lg mb-2">Waiting Card Number</h3>
                <p className="text-2xl font-bold text-green-600 mb-4">{waitingCardNumber}</p>
                <p className="text-sm text-muted-foreground">
                  Please save this waiting card number. It will be used to track the application status.
                </p>
              </div>
              
              <div className="space-y-2">
                <p><strong>Citizen:</strong> {citizenDetails?.full_names}</p>
                <p><strong>ID Number:</strong> {idNumber}</p>
                <p><strong>Payment Method:</strong> {paymentMethod === 'cash' ? 'Cash' : 'M-Pesa'}</p>
                <p className="text-sm text-muted-foreground">
                  Application submitted to admin for approval and dispatch.
                </p>
              </div>
              
              <Button 
                onClick={() => navigate('/officer/dashboard')}
                className="w-full"
              >
                Return to Dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default LostIdReplacement;