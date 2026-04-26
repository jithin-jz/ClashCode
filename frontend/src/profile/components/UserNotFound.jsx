import React from "react";
import { Users } from "lucide-react";
import { Button } from "../../components/ui/button";

const UserNotFound = ({ onBackHome }) => (
  <div className="h-screen w-full bg-[#000000] text-white flex flex-col items-center justify-center gap-6">
    <div className="text-center">
      <div className="w-20 h-20 rounded-xl bg-[#1a1a1a] border border-white/10 flex items-center justify-center mx-auto mb-6">
        <Users size={40} className="text-neutral-500" />
      </div>
      <h1 className="text-2xl font-semibold mb-2">User Not Found</h1>
      <p className="text-neutral-400 mb-6 text-sm">
        This user may have changed their username or doesn't exist.
      </p>
      <Button onClick={onBackHome} className="bg-white text-black hover:bg-zinc-200">
        Back to Home
      </Button>
    </div>
  </div>
);

export default UserNotFound;
