{{/* Имя чарта */}}
{{- define "materials-api.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Полное имя релиза */}}
{{- define "materials-api.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Общие метки */}}
{{- define "materials-api.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "materials-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Селекторы подов */}}
{{- define "materials-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "materials-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}