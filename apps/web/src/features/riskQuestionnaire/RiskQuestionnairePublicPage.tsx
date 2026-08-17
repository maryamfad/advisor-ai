import * as React from 'react'
import { useParams } from 'react-router-dom'

import {
  useQuestionnaireCatalog,
  useSubmitQuestionnaire,
  type SubmitResultResponse,
} from '@/api/riskQuestionnaire'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatEnumLabel } from '@/lib/format'

function ResultCard({ result }: { result: SubmitResultResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Thank you</CardTitle>
        <CardDescription>Your responses have been recorded.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          Based on your answers, your risk tolerance profile is{' '}
          <span className="font-semibold">{formatEnumLabel(result.risk_tolerance)}</span>. Your
          advisor will follow up to discuss what this means for your plan.
        </p>
      </CardContent>
    </Card>
  )
}

export function RiskQuestionnairePublicPage() {
  const { token } = useParams<{ token: string }>()
  const { data: catalog, isLoading, error } = useQuestionnaireCatalog(token ?? '')
  const submit = useSubmitQuestionnaire(token ?? '')
  const [answers, setAnswers] = React.useState<Record<string, string>>({})

  if (isLoading) {
    return <p className="text-center text-sm text-muted-foreground">Loading…</p>
  }

  const status = (error as { status?: number } | undefined)?.status
  if (status === 410) {
    return (
      <Alert>
        <AlertDescription>This questionnaire has already been completed.</AlertDescription>
      </Alert>
    )
  }
  if (error || !catalog) {
    return (
      <Alert variant="destructive">
        <AlertDescription>This questionnaire link is invalid.</AlertDescription>
      </Alert>
    )
  }

  if (submit.isSuccess) {
    return <ResultCard result={submit.data} />
  }

  const allAnswered = catalog.questions.every((question) => answers[question.key])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk tolerance questionnaire</CardTitle>
        <CardDescription>
          Answer honestly -- there are no right or wrong answers. This helps your advisor
          understand how comfortable you are with investment risk.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-8">
        {catalog.questions.map((question, index) => (
          <div key={question.key} className="flex flex-col gap-3">
            <p className="text-sm font-medium">
              {index + 1}. {question.text}
            </p>
            <RadioGroup
              value={answers[question.key]}
              onValueChange={(value) =>
                setAnswers((prev) => ({ ...prev, [question.key]: value }))
              }
            >
              {question.options.map((option) => (
                <div key={option.key} className="flex items-center gap-2">
                  <RadioGroupItem
                    value={option.key}
                    id={`${question.key}-${option.key}`}
                  />
                  <Label htmlFor={`${question.key}-${option.key}`} className="font-normal">
                    {option.text}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        ))}

        {submit.isError && (
          <Alert variant="destructive">
            <AlertDescription>
              {submit.error instanceof ApiError
                ? submit.error.message
                : 'Something went wrong submitting your answers.'}
            </AlertDescription>
          </Alert>
        )}

        <Button
          onClick={() => submit.mutate(answers)}
          disabled={!allAnswered || submit.isPending}
        >
          {submit.isPending ? 'Submitting…' : 'Submit answers'}
        </Button>
      </CardContent>
    </Card>
  )
}
