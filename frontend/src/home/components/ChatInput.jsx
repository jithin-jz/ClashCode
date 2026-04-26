import React, { memo, useState, useRef } from "react";
import { Send, Smile, X, Image } from "lucide-react";
import useChatStore from "../../stores/useChatStore";
import EmojiPicker from "emoji-picker-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

const ChatInput = ({
  user,
  sendMessage,
  showPicker,
  setShowPicker,
  inputRef,
  pickerRef,
  emojiButtonRef,
  sendTyping,
  placeholder,
}) => {
  const [inputMessage, setInputMessage] = React.useState("");
  const fileInputRef = React.useRef(null);
  const sendImage = useChatStore((s) => s.sendImage);

  const handleSend = () => {
    if (inputMessage.trim()) {
      sendMessage(inputMessage);
      setInputMessage("");
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      sendImage(file);
      // Reset input
      e.target.value = "";
    }
  };

  const handleEmojiClick = (emojiData) => {
    setInputMessage((prev) => prev + emojiData.emoji);
  };

  // Throttled typing indicator
  const lastTypingSent = React.useRef(0);
  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
    const now = Date.now();
    if (sendTyping && now - lastTypingSent.current > 2000) {
      lastTypingSent.current = now;
      sendTyping();
    }
  };

  return (
    <div className="relative px-5 py-4 bg-black/40 backdrop-blur-xl border-t border-white/5 space-y-3">
      {/* Emoji Picker */}
      {showPicker && (
        <div
          ref={pickerRef}
          className="absolute bottom-full left-0 w-full p-4 mb-2 z-50 animate-in fade-in slide-in-from-bottom-4 duration-500"
        >
          <div className="bg-black/80 backdrop-blur-2xl rounded-[2rem] border border-white/10 shadow-[0_30px_60px_rgba(0,0,0,0.8)] overflow-hidden h-[380px] flex">
            <EmojiPicker
              onEmojiClick={handleEmojiClick}
              theme="dark"
              width="100%"
              height="100%"
              lazyLoadEmojis={true}
              previewConfig={{ showPreview: false }}
              searchDisabled={false}
              skinTonesDisabled={true}
            />
          </div>
        </div>
      )}

      <div className="flex gap-3 items-center">
        {/* Emoji Button */}
        <button
          ref={emojiButtonRef}
          type="button"
          onClick={() => setShowPicker(!showPicker)}
          disabled={!user}
          className={`group relative flex items-center justify-center h-10 w-10 min-w-10 rounded-xl transition-all duration-300 ${
            showPicker
              ? "bg-white/10 text-white border-white/20"
              : "bg-white/[0.03] text-neutral-500 hover:text-neutral-200 border-transparent hover:border-white/10 hover:bg-white/5"
          } border disabled:opacity-20`}
        >
          {showPicker ? (
            <X size={18} />
          ) : (
            <Smile
              size={18}
              className="group-hover:scale-110 transition-transform"
            />
          )}
        </button>

        {/* Image Upload Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={!user}
          className="group relative flex items-center justify-center h-10 w-10 min-w-10 rounded-xl bg-white/[0.03] text-neutral-500 hover:text-neutral-200 border border-transparent hover:border-white/10 hover:bg-white/5 transition-all duration-300 disabled:opacity-20"
        >
          <Image
            size={18}
            className="group-hover:scale-110 transition-transform"
          />
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/*"
            onChange={handleImageUpload}
          />
        </button>

        {/* Input Wrapper */}
        <div className="relative flex-1 group">
          <div className="absolute -inset-[1px] bg-gradient-to-r from-emerald-500/0 via-emerald-500/20 to-emerald-500/0 rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
          <Input
            ref={inputRef}
            type="text"
            placeholder={
              user ? placeholder || "Forge a message..." : "Lock in to chat"
            }
            disabled={!user}
            value={inputMessage}
            onChange={handleInputChange}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            className="relative w-full bg-white/[0.03] border-white/5 focus-visible:border-emerald-500/30 rounded-xl px-4 h-10 text-white text-[12px] transition-all placeholder:text-neutral-600 focus-visible:ring-0 focus-visible:ring-offset-0 font-medium"
          />
        </div>

        {/* Send Button */}
        <button
          disabled={!user || !inputMessage.trim()}
          onClick={handleSend}
          className={`group relative flex items-center justify-center h-10 w-10 min-w-10 rounded-xl transition-all duration-500 overflow-hidden ${
            inputMessage.trim()
              ? "bg-emerald-500 text-black shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:scale-105 active:scale-95 border-transparent"
              : "bg-white/5 text-neutral-400 border border-white/10 hover:border-white/20 hover:text-white"
          } disabled:cursor-not-allowed`}
        >
          {inputMessage.trim() && (
            <div className="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          )}
          <Send
            size={16}
            className={`relative z-10 transition-transform duration-300 ${inputMessage.trim() ? "translate-x-0.5 -translate-y-0.5 rotate-[-10deg] group-hover:translate-x-1 group-hover:-translate-y-1" : ""}`}
          />
        </button>
      </div>

      {/* Bottom safety margin for mobile */}
      <div className="h-2 w-full sm:hidden" />
    </div>
  );
};

export default memo(ChatInput);
