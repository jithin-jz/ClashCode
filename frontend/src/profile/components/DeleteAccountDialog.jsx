import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";

const DeleteAccountDialog = ({ open, onOpenChange, onConfirm }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="bg-[#141414] border-[#404040]/30 text-white max-w-sm">
      <DialogHeader>
        <DialogTitle className="text-red-500">Delete Account</DialogTitle>
        <DialogDescription className="text-neutral-400">
          This action is permanent. All your battles, scores, and profile data will be purged.
        </DialogDescription>
      </DialogHeader>
      <DialogFooter className="gap-2 mt-4">
        <Button variant="ghost" onClick={() => onOpenChange(false)} className="text-neutral-400 hover:text-white">
          Cancel
        </Button>
        <Button onClick={onConfirm} className="bg-red-600 hover:bg-red-700 text-white">
          Permanently Delete
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default DeleteAccountDialog;
