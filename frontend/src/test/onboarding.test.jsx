// @vitest-environment happy-dom
// The first visit's questions on Home: answers kept as they are given, Back and Skip, the placement taps, and what
// Start writes where the rest of the app reads it.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import HomePanel from '../components/home/HomePanel'
import config from '../config/onboarding.json'
import knobs from '../config/home.json'
import { LEVEL_KEY, levelOf } from '../lib/learner/learnerLevel'
import { PLAN_KEY, readPlan } from '../lib/learner/plan'
import { GOAL_KEY } from '../lib/learner/rewards'
import { readRaw, writeRaw } from '../lib/store/stored'

const { copy } = config
const click = (role, name) => fireEvent.click(screen.getByRole(role, { name }))
const next = () => click('button', copy.continue)
const planNow = () => readPlan(readRaw(PLAN_KEY))
const home = (onGo = vi.fn()) => renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />) && onGo

describe('first-visit questions', () => {
  beforeEach(() => localStorage.clear())

  it('asks the first question, with Continue waiting for an answer', () => {
    home()
    expect(screen.getByRole('heading', { name: config.steps[0].question })).toBeTruthy()
    expect(screen.getByRole('button', { name: copy.continue }).disabled).toBe(true)
  })

  it('does not ask one who already has a level (sign-up, another device)', () => {
    writeRaw(LEVEL_KEY, 'intermediate')
    home()
    expect(screen.getByRole('region', { name: knobs.copy['fork-label'] })).toBeTruthy()
  })

  it('keeps an answer as it is given, shows its fact, and holds it when going back', () => {
    home()
    click('checkbox', /Understand the Qur/)
    expect(planNow().goals).toEqual(['understand'])
    expect(screen.getByText(/times the 382 words/)).toBeTruthy()
    next()
    click('radio', /Slowly/)
    click('button', copy.back)
    expect(screen.getByRole('checkbox', { name: /Understand the Qur/ }).getAttribute('aria-checked')).toBe('true')
  })

  it('lets two goals be picked and no third', () => {
    home()
    ;['Understand the Qur', 'Memorise the Qur', 'Speak with people'].forEach((name) => click('checkbox', new RegExp(name)))
    expect(planNow().goals).toEqual(['understand', 'memorise'])
  })

  it('skips to the three-level picker, once', () => {
    home()
    click('button', copy.skip)
    expect(screen.getByRole('region', { name: knobs.copy['fork-label'] })).toBeTruthy()
    expect(planNow().done).toBe(true)
  })

  it('places a reader by the taps, and lets the level said win instead', () => {
    const onGo = home()
    click('checkbox', /Understand the Qur/)
    next()
    click('radio', /Yes, comfortably/)
    next()
    click('radio', /A few words/)
    next()
    // Three taps, all right: level 3 by the check, level 1 by what was said.
    config.steps.find((step) => step.items).items.forEach((item) => {
      click('radio', item.options[item.right])
      next()
    })
    expect(planNow().check).toBe(3)
    for (const label of ['English', 'Not much yet', '10 min']) {
      click('radio', new RegExp(label))
      next()
    }
    expect(screen.getByText(copy['ready-title'])).toBeTruthy()
    click('button', /Use the level I said/)
    click('button', copy['ready-start'])
    expect(readRaw(LEVEL_KEY)).toBe('beginner')
    expect(readRaw(GOAL_KEY)).toBe('50')
    expect(planNow().done).toBe(true)
    expect(onGo).toHaveBeenCalledWith(...levelOf('beginner').start)
  })
})
