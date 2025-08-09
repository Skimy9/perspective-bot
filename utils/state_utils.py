# utils/state_utils.py
def reset_all_states(context):
    """Сбрасывает все состояния пользователя"""
    states_to_reset = ['nagual_state', 'current_test']
    
    for state in states_to_reset:
        if state in context.user_data:
            del context.user_data[state]
            logger.info(f"Состояние {state} сброшено")
    
    return True

def reset_nagual_state(context):
    """Сбрасывает состояние Пути к Скрытому"""
    if 'nagual_state' in context.user_data:
        del context.user_data['nagual_state']
        logger.info("Состояние nagual_state сброшено")
        return True
    return False
