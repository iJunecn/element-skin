<template>
  <span class="text-segments">
    <template v-for="(segment, index) in parsedSegments" :key="index">
      <a
        v-if="segment.type === 'link'"
        :class="linkClass"
        :href="segment.href"
        :target="segment.external ? '_blank' : undefined"
        :rel="segment.external ? 'noopener noreferrer' : undefined"
      >{{ segment.text }}</a>
      <span v-else>{{ segment.value }}</span>
    </template>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: {
    type: String,
    default: ''
  },
  siteName: {
    type: String,
    default: ''
  },
  linkClass: {
    type: String,
    default: ''
  }
})

const parsedSegments = computed(() => parseFooterText(props.text, props.siteName))

function parseFooterText(rawText, currentSiteName) {
  if (!rawText) return []
  const siteLabel = (currentSiteName || '').trim()
  const segments = []
  const parts = rawText.split('{site}')

  for (let index = 0; index < parts.length; index += 1) {
    appendMarkdownSegments(parts[index], segments)
    if (index < parts.length - 1 && siteLabel) {
      segments.push({ type: 'link', text: siteLabel, href: '/', external: false })
    }
  }

  return segments
}

function appendMarkdownSegments(text, segments) {
  const pattern = /\[([^\]]+)\]\(([^)]+)\)/g
  let lastIndex = 0
  let match

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', value: text.slice(lastIndex, match.index) })
    }

    const linkText = match[1].trim()
    const href = match[2].trim()
    if (linkText && linkText.length <= 128 && isSafeHref(href)) {
      const isExternal = href.startsWith('http://') || href.startsWith('https://')
      segments.push({ type: 'link', text: linkText, href, external: isExternal })
    } else {
      segments.push({ type: 'text', value: match[0] })
    }

    lastIndex = pattern.lastIndex
  }

  if (lastIndex < text.length) {
    segments.push({ type: 'text', value: text.slice(lastIndex) })
  }
}

function isSafeHref(href) {
  if (!href || href.length > 2048) return false
  if (href.startsWith('/')) return true
  const normalized = href.toLowerCase()
  return normalized.startsWith('http://') || normalized.startsWith('https://')
}
</script>
