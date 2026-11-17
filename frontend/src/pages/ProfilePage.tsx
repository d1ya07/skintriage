import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

export default function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;

  const rows = [
    ["Name", user.name],
    ["Email", user.email],
    ["Skin type", user.skin_type ?? "Not specified"],
    ["Account status", user.is_active ? "Active" : "Disabled"],
    ["Member since", new Date(user.created_at).toLocaleDateString()],
  ];

  return (
    <Card className="mx-auto max-w-xl">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-2xl">My profile</CardTitle>
        <Badge className="capitalize">{user.role}</Badge>
      </CardHeader>
      <CardContent>
        <dl className="divide-y">
          {rows.map(([label, value]) => (
            <div key={label} className="flex justify-between py-3 text-sm">
              <dt className="text-muted-foreground">{label}</dt>
              <dd className="font-medium">{value}</dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
