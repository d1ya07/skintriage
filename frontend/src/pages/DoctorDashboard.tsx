import { CalendarClock } from "lucide-react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function DoctorDashboard() {
  const { user } = useAuth();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Welcome, {user?.name}</h1>
        <p className="text-muted-foreground">Doctor workspace</p>
      </div>
      <Card>
        <CardHeader>
          <CalendarClock className="size-6" />
          <CardTitle className="pt-2">Your appointments</CardTitle>
          <CardDescription>
            Your schedule with confirm and complete actions arrives in Phase 4.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" asChild>
            <Link to="/profile">View profile</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
