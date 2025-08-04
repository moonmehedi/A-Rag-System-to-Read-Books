"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { ChevronRight, ChevronDown, MessageSquare, Menu, Send, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { useRouter } from "next/navigation"

const DEFAULT_AI_RESPONSE = `In recent decades, artificial intelligence (AI) has dramatically transformed numerous industries, from healthcare to finance, by automating complex decision-making processes. One key component of this transformation is machine learning, a subset of AI that enables systems to learn from data and improve over time without being explicitly programmed. Within machine learning, neural networks have become particularly prominent due to their ability to process vast amounts of information in layers, much like the human brain. These networks power applications like image recognition, speech synthesis, and natural language processing. While AI offers significant benefits, including efficiency and scalability, it also raises concerns about privacy, bias, and job displacement. Therefore, responsible development and deployment of AI technologies are crucial for ensuring that they serve the broader interests of society.`

interface Message {
  id: string
  content: string
  timestamp: Date
  isUserMessage: boolean
}

interface Chat {
  id: string;
  parentId: string | null;
  title: string;
  messages: Message[];
  children: string[];
  path: string[];
  level: number;
  selectedText?: string; // Optional selected text for follow-up questions
}

interface ChatState {
  [key: string]: Chat;
}

interface SelectionTooltip {
  show: boolean
  x: number
  y: number
  selectedText: string
  messageId: string
  chatId: string
}

export default function NestedChatInterface() {
  const router = useRouter();
  const [chats, setChats] = useState<ChatState>({});
  const [currentChatId, setCurrentChatId] = useState<string>("root");
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [inputValue, setInputValue] = useState("")
  const [selectionTooltip, setSelectionTooltip] = useState<SelectionTooltip>({
    show: false,
    x: 0,
    y: 0,
    selectedText: "",
    messageId: "",
    chatId: "",
  })
  const [uploadedDocId, setUploadedDocId] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [selectedPdfName, setSelectedPdfName] = useState<string>("")
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // Initialize root chat
  useEffect(() => {
    const rootChat: Chat = {
      id: "root",
      parentId: null,
      title: "Main Chat",
      messages: [
        {
          id: "msg-1",
          content: DEFAULT_AI_RESPONSE,
          timestamp: new Date(),
          isUserMessage: false,
        },
      ],
      children: [],
      path: ["parent 0"],
      level: 0,
    }

    setChats({ root: rootChat })
  }, [])

  const generateChatId = () => `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  const generateMessageId = () => `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

  // Handle text selection with improved detection
  const handleSelectionChange = useCallback(() => {
    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) {
      setSelectionTooltip((prev) => ({ ...prev, show: false }))
      return
    }

    const selectedText = selection.toString().trim()
    if (selectedText.length === 0) {
      setSelectionTooltip((prev) => ({ ...prev, show: false }))
      return
    }

    // Find the message element that contains the selection
    const range = selection.getRangeAt(0)
    const messageElement =
      range.commonAncestorContainer.nodeType === Node.TEXT_NODE
        ? range.commonAncestorContainer.parentElement?.closest("[data-message-id]")
        : range.commonAncestorContainer instanceof Element
          ? range.commonAncestorContainer.closest("[data-message-id]")
          : null

    if (!messageElement) {
      setSelectionTooltip((prev) => ({ ...prev, show: false }))
      return
    }

    const messageId = messageElement.getAttribute("data-message-id")
    const chatId = messageElement.getAttribute("data-chat-id")

    if (!messageId || !chatId) {
      setSelectionTooltip((prev) => ({ ...prev, show: false }))
      return
    }

    // Get selection position
    const rect = range.getBoundingClientRect()
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop

    setSelectionTooltip({
      show: true,
      x: rect.left + rect.width / 2,
      y: rect.top + scrollTop - 10,
      selectedText,
      messageId,
      chatId,
    })
  }, [])

  // Set up selection event listeners
  useEffect(() => {
    document.addEventListener("selectionchange", handleSelectionChange)
    return () => {
      document.removeEventListener("selectionchange", handleSelectionChange)
    }
  }, [handleSelectionChange])

  const createSubchatFromSelection = () => {
    const parentChat = chats[selectionTooltip.chatId]
    if (!parentChat || !selectionTooltip.selectedText) return

    const newChatId = generateChatId()
    const subchatLevel = parentChat.level + 1
    const newPath = [...parentChat.path, `subchat ${subchatLevel}`]

    const truncatedSelection =
      selectionTooltip.selectedText.length > 50
        ? selectionTooltip.selectedText.substring(0, 50) + "..."
        : selectionTooltip.selectedText

    const pathString = newPath.join(" → ")
    const title = `${pathString} (selection: '${truncatedSelection}')`

    const newChat: Chat = {
      id: newChatId,
      parentId: selectionTooltip.chatId,
      title,
      messages: [
        {
          id: generateMessageId(),
          content: DEFAULT_AI_RESPONSE,
          timestamp: new Date(),
          isUserMessage: false,
        },
      ],
      children: [],
      path: newPath,
      selectedText: selectionTooltip.selectedText,
      level: subchatLevel,
    }

    setChats((prev) => ({
      ...prev,
      [newChatId]: newChat,
      [selectionTooltip.chatId]: {
        ...prev[selectionTooltip.chatId],
        children: [...prev[selectionTooltip.chatId].children, newChatId],
      },
    }))

    setCurrentChatId(newChatId)
    setSelectionTooltip((prev) => ({ ...prev, show: false }))

    // Clear selection
    window.getSelection()?.removeAllRanges()
  }

  // PDF upload handler
  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setSelectedPdfName(file.name)
    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)
    try {
      const response = await fetch("http://localhost:8000/rag/upload-doc", {
        method: "POST",
        body: formData,
      })
      const data = await response.json()
      if (data.doc_id) {
        setUploadedDocId(data.doc_id)
        alert("PDF uploaded and chunked successfully!")
      } else {
        alert("Failed to upload PDF: " + (data.error || "Unknown error"))
      }
    } catch (err) {
      alert("Error uploading PDF")
    } finally {
      setUploading(false)
    }
  }

  // Fetch chat tree on mount
  useEffect(() => {
    const fetchChatTree = async () => {
      const token = localStorage.getItem("jwt");
      if (!token) {
        router.push("/"); // Redirect to login if no token
        return;
      }

      try {
        const res = await fetch("http://localhost:8000/chat/tree", {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        if (!res.ok) {
          if (res.status === 401) {
            localStorage.removeItem("jwt");
            router.push("/");
            return;
          }
          throw new Error("Failed to fetch chat history");
        }

        const data = await res.json();
        
        // Transform flat message list into chat tree
        const chatMap: ChatState = {};
        data.forEach((msg: any) => {
          const chatId = msg.id;
          if (!chatMap[chatId]) {
            chatMap[chatId] = {
              id: chatId,
              parentId: msg.parent_id,
              title: msg.ltree_path.split('.').pop() || 'Chat',
              messages: [],
              children: [],
              path: msg.ltree_path.split('.'),
              level: msg.ltree_path.split('.').length - 1,
            };
          }

          // Add message to chat
          chatMap[chatId].messages.push({
            id: msg.id,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            isUserMessage: msg.is_user,
          });

          // Link parent-child relationships
          if (msg.parent_id && chatMap[msg.parent_id]) {
            if (!chatMap[msg.parent_id].children.includes(chatId)) {
              chatMap[msg.parent_id].children.push(chatId);
            }
          }
        });

        // Find root chat or create one
        if (Object.keys(chatMap).length === 0) {
          chatMap.root = {
            id: "root",
            parentId: null,
            title: "Main Chat",
            messages: [],
            children: [],
            path: ["Main"],
            level: 0,
          };
        }

        setChats(chatMap);
        // Set current chat to most recent or root
        const lastChat = data[data.length - 1];
        setCurrentChatId(lastChat ? lastChat.id : "root");
      } catch (error) {
        console.error("Error fetching chat history:", error);
        // Fallback to empty root chat
        setChats({
          root: {
            id: "root",
            parentId: null,
            title: "Main Chat",
            messages: [],
            children: [],
            path: ["Main"],
            level: 0,
          },
        });
      }
    };

    fetchChatTree();
  }, [router]);

  const sendMessage = async () => {
    if (!inputValue.trim() || !chats[currentChatId] || sending) return;
    
    const token = localStorage.getItem("jwt");
    if (!token) {
      router.push("/");
      return;
    }

    setSending(true);
    const messageText = inputValue;
    setInputValue(""); // Clear input immediately

    // Add user message immediately, but only once per send
    setChats((prev) => {
      const updates = { ...prev };
      const currentChat = updates[currentChatId];
      // Only add if the last message is not the same as the new one
      const lastMsg = currentChat.messages[currentChat.messages.length - 1];
      if (!lastMsg || lastMsg.content !== messageText || !lastMsg.isUserMessage) {
        currentChat.messages.push({
          id: generateMessageId(),
          content: messageText,
          timestamp: new Date(),
          isUserMessage: true,
        });
      }
      return updates;
    });

    try {
      const formData = new FormData();
      formData.append("question", messageText);
      formData.append("chat_id", currentChatId);
      if (uploadedDocId) {
        formData.append("doc_id", uploadedDocId);
      }
      const res = await fetch("http://localhost:8000/rag/chat", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data = await res.json();
      // Only add AI response if it is not already present (prevent duplication)
      setChats((prev) => {
        const updates = { ...prev };
        const currentChat = updates[currentChatId];
        const lastMsg = currentChat.messages[currentChat.messages.length - 1];
        if (!lastMsg || lastMsg.id !== data.ai_message.id) {
          currentChat.messages.push({
            id: data.ai_message.id,
            content: data.ai_message.content,
            timestamp: new Date(data.ai_message.timestamp),
            isUserMessage: false,
          });
        }
        return updates;
      });
    } catch (error) {
      console.error("Error sending message:", error);
      alert("Failed to send message. Please try again.");
    } finally {
      setSending(false);
    }
  }

  const navigateToChat = (chatId: string) => {
    setCurrentChatId(chatId)
    setSelectionTooltip((prev) => ({ ...prev, show: false }))
  }

  const navigateToPathLevel = (levelIndex: number) => {
    const currentChat = chats[currentChatId]
    if (!currentChat) return

    let targetChatId = currentChatId
    let targetChat = currentChat

    while (targetChat && targetChat.path.length > levelIndex + 1) {
      if (targetChat.parentId) {
        targetChatId = targetChat.parentId
        targetChat = chats[targetChatId]
      } else {
        break
      }
    }

    setCurrentChatId(targetChatId)
  }

  // Hide tooltip when clicking elsewhere
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Element
      if (!target.closest("[data-tooltip]")) {
        setSelectionTooltip((prev) => ({ ...prev, show: false }))
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const currentChat = chats[currentChatId]
  const visibleChats = getVisibleChatHierarchy(chats, currentChatId)

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100 relative">
      {/* Selection Tooltip */}
      {selectionTooltip.show && (
        <div
          data-tooltip
          className="fixed z-50 animate-in fade-in-0 zoom-in-95 duration-200"
          style={{
            left: selectionTooltip.x,
            top: selectionTooltip.y,
            transform: "translate(-50%, -100%)",
          }}
        >
          <div className="bg-gray-900 text-white px-4 py-2 rounded-lg shadow-xl border border-gray-700">
            <button
              onClick={createSubchatFromSelection}
              className="flex items-center gap-2 hover:text-blue-300 transition-colors text-sm font-medium"
            >
              <Plus className="h-3 w-3" />
              Ask follow-up
            </button>
          </div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
        </div>
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "bg-white/80 backdrop-blur-sm border-r border-gray-200/50 transition-all duration-300 z-10 shadow-lg",
          sidebarOpen ? "w-80" : "w-0 overflow-hidden",
        )}
      >
        <div className="p-6 border-b border-gray-200/50 bg-white/50">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-800">Conversations</h2>
            <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(false)} className="hover:bg-gray-100">
              <Menu className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="p-4 overflow-y-auto h-full">
          <ChatTreeNode
            chatId="root"
            chats={chats}
            currentChatId={currentChatId}
            onNavigate={navigateToChat}
            level={0}
          />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 p-6 z-10 shadow-sm">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(true)} className="hover:bg-gray-100">
                <Menu className="h-4 w-4" />
              </Button>
            )}
            {currentChat && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                {currentChat.path.map((segment, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <button
                      onClick={() => navigateToPathLevel(index)}
                      className="hover:text-blue-600 hover:underline transition-colors font-medium px-2 py-1 rounded hover:bg-blue-50"
                    >
                      {segment}
                    </button>
                    {index < currentChat.path.length - 1 && <ChevronRight className="h-4 w-4 text-gray-400" />}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Chat Panels Container */}
        <div className="flex-1 flex overflow-x-auto overflow-y-hidden bg-gradient-to-r from-gray-50 to-white">
          {visibleChats.map((chat, index) => (
            <ChatPanel
              key={chat.id}
              chat={chat}
              isActive={chat.id === currentChatId}
              onNavigate={navigateToChat}
              style={{
                marginLeft: `${chat.level * 24}px`,
                minWidth: "500px",
                maxWidth: "600px",
              }}
            />
          ))}
        </div>

        {/* Input Area */}
        <div className="bg-white/90 backdrop-blur-sm border-t border-gray-200/50 p-6 z-10 shadow-lg">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type your message..."
                  onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                  className="pr-12 py-3 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500 rounded-xl shadow-sm"
                />
                <Button
                  onClick={sendMessage}
                  size="sm"
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 rounded-lg bg-blue-600 hover:bg-blue-700"
                  disabled={!inputValue.trim() || uploading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              {/* PDF Upload Button */}
              <div className="flex flex-col items-center ml-2">
                <label htmlFor="pdf-upload" className="cursor-pointer bg-gray-200 hover:bg-gray-300 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium border border-gray-300 shadow-sm">
                  {uploading ? "Uploading..." : "Upload PDF"}
                </label>
                <input
                  id="pdf-upload"
                  type="file"
                  accept="application/pdf"
                  style={{ display: 'none' }}
                  onChange={handlePdfUpload}
                  disabled={uploading}
                />
                <span className="text-xs mt-1 text-gray-500 min-h-[1em]">
                  {selectedPdfName ? selectedPdfName : "No file chosen"}
                </span>
                {uploadedDocId && <span className="text-xs text-green-600 mt-1">PDF ready for Q&A</span>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function getVisibleChatHierarchy(chats: ChatState, currentChatId: string): Chat[] {
  const result: Chat[] = [];
  const currentChat = chats[currentChatId];

  if (!currentChat) {
    return result;
  }

  // Get the path from root to current chat
  const pathChats: Chat[] = [];
  let chat: Chat | null = currentChat;

  while (chat) {
    pathChats.unshift(chat);
    chat = chat.parentId ? chats[chat.parentId] : null;
  }

  return pathChats;
}

interface ChatPanelProps {
  chat: Chat
  isActive: boolean
  onNavigate: (chatId: string) => void
  style?: React.CSSProperties
}

function ChatPanel({ chat, isActive, onNavigate, style }: ChatPanelProps) {
  const formatMessageContent = (content: string) => {
    // Split content into paragraphs and process each one
    return content.split('\n\n').map((paragraph, i) => {
      // Check if this is an equation paragraph
      if (paragraph.startsWith('Equation:')) {
        const equation = paragraph.replace('Equation:', '').trim();
        return (
          <div key={i} className="bg-gray-100 p-3 rounded-lg my-2 font-mono text-sm overflow-x-auto">
            {equation}
          </div>
        );
      }
      
      // Regular text paragraph
      return (
        <p key={i} className="mb-2">
          {paragraph}
        </p>
      );
    });
  };

  return (
    <div
      className={cn(
        "flex-shrink-0 border-r border-gray-200/50 bg-white/60 backdrop-blur-sm transition-all duration-300 shadow-sm",
        isActive ? "opacity-100 bg-white/80" : "opacity-80 hover:opacity-90",
      )}
      style={style}
    >
      <div className="h-full flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200/50 bg-gradient-to-r from-gray-50/50 to-white/50">
          <h3 className="text-sm font-semibold text-gray-700 truncate">{chat.title}</h3>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {chat.messages.map((message) => (
            <div
              key={message.id}
              className={cn("group", message.isUserMessage ? "flex justify-end" : "flex justify-start")}
            >
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-4 py-3 shadow-sm transition-all duration-200",
                  message.isUserMessage
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-200 text-gray-800 hover:shadow-md",
                )}
                data-message-id={message.id}
                data-chat-id={chat.id}
              >
                <div className="text-sm leading-relaxed whitespace-pre-wrap select-text">
                  {formatMessageContent(message.content)}
                </div>
                <div className={cn("mt-2 text-xs", message.isUserMessage ? "text-blue-100" : "text-gray-500")}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface ChatTreeNodeProps {
  chatId: string
  chats: ChatState
  currentChatId: string
  onNavigate: (chatId: string) => void
  level: number
}

function ChatTreeNode({ chatId, chats, currentChatId, onNavigate, level }: ChatTreeNodeProps) {
  const [expanded, setExpanded] = useState(true)
  const chat = chats[chatId]

  if (!chat) return null

  const hasChildren = chat.children.length > 0
  const isActive = currentChatId === chatId

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 p-3 rounded-xl cursor-pointer hover:bg-gray-100/80 transition-all duration-200 group",
          isActive && "bg-blue-50 text-blue-700 shadow-sm border border-blue-200",
        )}
        style={{ marginLeft: `${level * 20}px` }}
        onClick={() => onNavigate(chatId)}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setExpanded(!expanded)
            }}
            className="p-1 hover:bg-gray-200 rounded-md transition-colors"
          >
            {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </button>
        )}
        {!hasChildren && <div className="w-5" />}
        <MessageSquare className="h-4 w-4 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">{chat.path[chat.path.length - 1]}</div>
          {chat.selectedText && (
            <div className="text-xs text-gray-500 truncate mt-1">
              "{chat.selectedText.length > 40 ? chat.selectedText.substring(0, 40) + "..." : chat.selectedText}"
            </div>
          )}
        </div>
      </div>

      {hasChildren && expanded && (
        <div className="transition-all duration-200 space-y-1 mt-1">
          {chat.children.map((childId) => (
            <ChatTreeNode
              key={childId}
              chatId={childId}
              chats={chats}
              currentChatId={currentChatId}
              onNavigate={onNavigate}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
