import * as React from 'react'
import { Wrench } from 'lucide-react'

import {
  useConversations,
  useConversation,
  useCreateConversation,
  useSendMessage,
  AssistantUnavailableError,
  type AiMessage,
} from '@/api/aiAssistant'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'
import { formatDateTime } from '@/lib/format'

function ToolCallDetail({ message }: { message: AiMessage }) {
  let output: unknown = message.content
  try {
    output = JSON.parse(message.content)
  } catch {
    // content wasn't JSON -- fall back to showing it raw
  }

  return (
    <details className="rounded-md border bg-muted/40 px-3 py-2 text-xs">
      <summary className="flex cursor-pointer items-center gap-1.5 font-medium text-muted-foreground">
        <Wrench className="size-3.5" />
        used {message.tool_name}
      </summary>
      <div className="mt-2 grid gap-2">
        {message.tool_input && (
          <div>
            <div className="text-muted-foreground">Input</div>
            <pre className="overflow-x-auto rounded bg-background p-2">
              {JSON.stringify(message.tool_input, null, 2)}
            </pre>
          </div>
        )}
        <div>
          <div className="text-muted-foreground">Output</div>
          <pre className="overflow-x-auto rounded bg-background p-2">
            {JSON.stringify(output, null, 2)}
          </pre>
        </div>
      </div>
    </details>
  )
}

function MessageBubble({ message }: { message: AiMessage }) {
  if (message.role === 'tool') {
    return <ToolCallDetail message={message} />
  }

  const isUser = message.role === 'user'

  return (
    <div className={cn('flex flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}
      >
        {message.content}
      </div>
      <span className="text-[10px] text-muted-foreground">
        {formatDateTime(message.created_at)}
      </span>
    </div>
  )
}

export function AssistantTab({ clientId }: { clientId: number }) {
  const { data: conversations } = useConversations(clientId)
  const createConversation = useCreateConversation(clientId)
  const [explicitConversationId, setConversationId] = React.useState<number | null>(null)
  const conversationId = explicitConversationId ?? conversations?.[0]?.id ?? null
  const { data: conversation, isLoading: loadingConversation } = useConversation(
    clientId,
    conversationId
  )
  const sendMessage = useSendMessage(clientId, conversationId ?? -1)
  const [draft, setDraft] = React.useState('')
  const scrollRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [conversation?.messages.length])

  async function handleSend() {
    if (!draft.trim() || conversationId === null) return
    const message = draft
    setDraft('')
    await sendMessage.mutateAsync(message)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>AI assistant</CardTitle>
        <div className="flex items-center gap-2">
          {conversations && conversations.length > 0 && (
            <Select
              value={conversationId ? String(conversationId) : undefined}
              onValueChange={(value) => setConversationId(Number(value))}
            >
              <SelectTrigger className="w-56">
                <SelectValue placeholder="Select a conversation" />
              </SelectTrigger>
              <SelectContent>
                {conversations.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    Started {formatDateTime(c.started_at)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              const created = await createConversation.mutateAsync()
              setConversationId(created.id)
            }}
            disabled={createConversation.isPending}
          >
            New conversation
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {conversationId === null ? (
          <p className="text-sm text-muted-foreground">
            Start a new conversation to ask about this client.
          </p>
        ) : (
          <>
            <div ref={scrollRef} className="flex max-h-[28rem] flex-col gap-3 overflow-y-auto">
              {loadingConversation ? (
                <p className="text-sm text-muted-foreground">Loading…</p>
              ) : conversation?.messages.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No messages yet -- ask something below.
                </p>
              ) : (
                conversation?.messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))
              )}
            </div>

            {sendMessage.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {sendMessage.error instanceof AssistantUnavailableError
                    ? sendMessage.error.message
                    : 'Something went wrong sending that message.'}
                </AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Input
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask about this client…"
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    void handleSend()
                  }
                }}
                disabled={sendMessage.isPending}
              />
              <Button onClick={handleSend} disabled={sendMessage.isPending || !draft.trim()}>
                {sendMessage.isPending ? 'Sending…' : 'Send'}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
